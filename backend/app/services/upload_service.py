"""
Orquestra o pipeline completo de upload: validar → preview → processar → salvar.
"""
import uuid
from datetime import date
from typing import Optional
import pandas as pd

from ..core.database import get_service_client
from ..schemas.uploads import UploadPreview
from .excel_reader import (
    read_excel_file, validate_columns, preview_data, get_column_list
)
from .mapa_service import processar_mapa, df_to_itens

# DIÁRIAS: sempre auto-substituem o upload do mesmo dia
DIARIAS_TIPOS = {"mapa_vendas", "lista_precos", "estoque", "dde", "meta_vendedor"}
# FIXAS: substituem todos os dados ao re-importar
FIXAS_TIPOS = {"planilha_clientes", "planilha_produtos", "base_categorias", "tipos_tabela_preco", "vendedores"}


def criar_upload_registro(tipo: str, arquivo: str, usuario: str = "admin") -> str:
    db = get_service_client()
    upload_id = str(uuid.uuid4())
    db.table("uploads").insert({
        "id": upload_id,
        "tipo": tipo,
        "arquivo_original": arquivo,
        "usuario": usuario,
        "status": "pendente",
    }).execute()
    return upload_id


def atualizar_status_upload(upload_id: str, status: str, **kwargs):
    db = get_service_client()
    payload = {"status": status, **kwargs}
    db.table("uploads").update(payload).eq("id", upload_id).execute()


def log_upload(upload_id: str, nivel: str, mensagem: str, linha: Optional[int] = None):
    db = get_service_client()
    db.table("upload_logs").insert({
        "upload_id": upload_id,
        "nivel": nivel,
        "mensagem": mensagem,
        "linha": linha,
    }).execute()


async def processar_upload(
    content: bytes,
    tipo: str,
    data_referencia: Optional[date],
    arquivo_nome: str,
    usuario: str = "admin",
    _substituir: bool = False,
) -> UploadPreview:
    """Fase 1: Lê o arquivo, valida colunas e retorna preview sem salvar dados."""
    upload_id = criar_upload_registro(tipo, arquivo_nome, usuario)
    atualizar_status_upload(upload_id, "processando")

    try:
        df, avisos = read_excel_file(content, tipo)
    except ValueError as e:
        atualizar_status_upload(upload_id, "erro", mensagem_erro=str(e))
        log_upload(upload_id, "error", str(e))
        return UploadPreview(
            upload_id=upload_id,
            tipo=tipo,
            total_registros=0,
            colunas_encontradas=[],
            colunas_ausentes=[],
            avisos=[],
            erros=[str(e)],
            preview_linhas=[],
            pode_importar=False,
        )

    colunas_ausentes = validate_columns(df, tipo)
    erros: list[str] = []
    if colunas_ausentes:
        erros.append(f"Colunas obrigatórias ausentes: {', '.join(colunas_ausentes)}")

    pode_importar = len(erros) == 0
    atualizar_status_upload(
        upload_id, "aguardando" if pode_importar else "erro",
        total_registros=len(df),
        mensagem_erro="; ".join(erros) if erros else None,
        data_referencia=str(data_referencia) if data_referencia else None,
    )

    return UploadPreview(
        upload_id=upload_id,
        tipo=tipo,
        total_registros=len(df),
        colunas_encontradas=get_column_list(df),
        colunas_ausentes=colunas_ausentes,
        avisos=avisos,
        erros=erros,
        preview_linhas=preview_data(df, 5),
        pode_importar=pode_importar,
    )


async def confirmar_importacao(
    upload_id: str,
    content: bytes,
    tipo: str,
    data_referencia: Optional[date],
    substituir: bool = False,
) -> dict:
    """Fase 2: Efetiva a importação após confirmação."""
    db = get_service_client()
    atualizar_status_upload(upload_id, "processando")

    # DIÁRIAS sempre auto-substituem o mesmo dia
    if tipo in DIARIAS_TIPOS:
        substituir = True

    try:
        df, _ = read_excel_file(content, tipo)
    except Exception as e:
        atualizar_status_upload(upload_id, "erro", mensagem_erro=str(e))
        return {"ok": False, "mensagem": str(e)}

    try:
        if tipo == "mapa_vendas":
            return await _salvar_mapa_vendas(db, upload_id, df, data_referencia, substituir)
        elif tipo == "planilha_produtos":
            return await _salvar_produtos(db, upload_id, df, tipo, data_referencia)
        elif tipo == "planilha_clientes":
            return await _salvar_clientes(db, upload_id, df, tipo, data_referencia)
        elif tipo == "lista_precos":
            return await _salvar_precos(db, upload_id, df, data_referencia, substituir)
        elif tipo == "estoque":
            return await _salvar_estoque(db, upload_id, df, data_referencia, substituir)
        elif tipo == "dde":
            return await _salvar_dde(db, upload_id, df, data_referencia, substituir)
        elif tipo == "base_categorias":
            return await _salvar_base_categorias(db, upload_id, df, data_referencia)
        elif tipo == "tipos_tabela_preco":
            return await _salvar_tipos_tabela_preco(db, upload_id, df, data_referencia)
        elif tipo == "vendedores":
            return await _salvar_vendedores(db, upload_id, df, data_referencia)
        elif tipo == "tabela_cliente_rota":
            return await _salvar_tabela_cliente_rota(db, upload_id, df, data_referencia)
        elif tipo == "tabela_fretes":
            return await _salvar_tabela_fretes(db, upload_id, df, data_referencia)
        elif tipo == "tabela_grupo_rede":
            return await _salvar_tabela_grupo_rede(db, upload_id, df, data_referencia)
        elif tipo == "tabela_supervisor_vendedor":
            return await _salvar_tabela_supervisor_vendedor(db, upload_id, df, data_referencia)
        elif tipo == "meta_vendedor":
            return await _salvar_meta_vendedor(db, upload_id, df, data_referencia, substituir)
        else:
            return {"ok": False, "mensagem": f"Tipo '{tipo}' não suportado."}
    except Exception as e:
        atualizar_status_upload(upload_id, "erro", mensagem_erro=str(e))
        log_upload(upload_id, "error", str(e))
        return {"ok": False, "mensagem": str(e)}


# ─── Salvar DIÁRIAS ──────────────────────────────────────────────────────────

async def _salvar_mapa_vendas(db, upload_id: str, df: pd.DataFrame,
                               data_referencia: Optional[date], substituir: bool) -> dict:
    data_ref = data_referencia or date.today()
    existing = db.table("mapa_vendas_uploads").select("id").eq(
        "data_referencia", str(data_ref)
    ).execute()

    if existing.data:
        if not substituir:
            return {"ok": False, "mensagem": f"Já existe Mapa de Vendas para {data_ref}.", "ja_existe": True}
        old_id = existing.data[0]["id"]
        db.table("mapa_vendas_itens").delete().eq("mapa_upload_id", old_id).execute()
        db.table("mapa_vendas_uploads").delete().eq("id", old_id).execute()
        log_upload(upload_id, "info", f"Upload anterior de {data_ref} substituído.")

    df_produtos = _buscar_produtos_vigentes(db)
    df_clientes = _buscar_clientes_vigentes(db)
    df_precos = _buscar_precos(db)
    df_estoque = _buscar_estoque(db)
    params_logistica = _buscar_params_logistica(db)

    df_proc = processar_mapa(df, df_produtos, df_clientes, df_precos, df_estoque, params_logistica)

    mapa_upload = db.table("mapa_vendas_uploads").insert({
        "upload_id": upload_id,
        "data_referencia": str(data_ref),
    }).execute()
    mapa_upload_id = mapa_upload.data[0]["id"]

    itens = df_to_itens(df_proc, mapa_upload_id, data_ref)
    batch_size = 500
    for i in range(0, len(itens), batch_size):
        db.table("mapa_vendas_itens").insert(itens[i:i + batch_size]).execute()

    _atualizar_fato_vendas(db, df_proc, upload_id, data_ref)

    total = len(itens)
    atualizar_status_upload(
        upload_id, "concluido",
        total_registros=total,
        registros_processados=total,
        data_referencia=str(data_ref),
    )
    return {"ok": True, "mensagem": f"{total} itens processados com sucesso.", "upload_id": upload_id}


async def _salvar_precos(db, upload_id: str, df: pd.DataFrame,
                          data_ref: Optional[date], substituir: bool) -> dict:
    data_ref_str = str(data_ref or date.today())
    existing = db.table("lista_precos_uploads").select("id").eq("data_referencia", data_ref_str).execute()
    if existing.data:
        if not substituir:
            return {"ok": False, "mensagem": f"Já existe Lista de Preços para {data_ref_str}.", "ja_existe": True}
        for old in existing.data:
            db.table("lista_precos_itens").delete().eq("lp_upload_id", old["id"]).execute()
            db.table("lista_precos_uploads").delete().eq("id", old["id"]).execute()

    lp = db.table("lista_precos_uploads").insert({
        "upload_id": upload_id,
        "data_referencia": data_ref_str,
    }).execute()
    lp_id = lp.data[0]["id"]

    campos = ["cod_tabela", "codigo", "descricao", "unidade", "preco_base",
              "preco_venda", "vlr_desconto", "data_inicial", "data_final", "estado", "tipo_operacao"]
    rows = []
    for _, r in df.iterrows():
        row: dict = {"lp_upload_id": lp_id, "data_referencia": data_ref_str}
        for c in campos:
            val = r.get(c)
            if val is not None and str(val) not in ("nan", "None", ""):
                row[c] = str(val) if isinstance(val, date) else val
        rows.append(row)

    batch_size = 500
    for i in range(0, len(rows), batch_size):
        db.table("lista_precos_itens").insert(rows[i:i + batch_size]).execute()

    atualizar_status_upload(upload_id, "concluido", total_registros=len(rows), registros_processados=len(rows))
    return {"ok": True, "mensagem": f"{len(rows)} preços importados.", "upload_id": upload_id}


async def _salvar_estoque(db, upload_id: str, df: pd.DataFrame,
                           data_ref: Optional[date], substituir: bool) -> dict:
    data_ref_str = str(data_ref or date.today())
    existing = db.table("estoque_uploads").select("id").eq("data_referencia", data_ref_str).execute()
    if existing.data:
        if not substituir:
            return {"ok": False, "mensagem": f"Já existe Estoque para {data_ref_str}.", "ja_existe": True}
        for old in existing.data:
            db.table("estoque_itens").delete().eq("est_upload_id", old["id"]).execute()
            db.table("estoque_uploads").delete().eq("id", old["id"]).execute()

    est = db.table("estoque_uploads").insert({
        "upload_id": upload_id, "data_referencia": data_ref_str,
    }).execute()
    est_id = est.data[0]["id"]

    campos = ["codigo", "descricao", "unidade", "filial", "armz",
              "ult_preco", "custo_unitario", "estoque_kg", "valor_estoque",
              "nome_empresa", "nome_filial"]
    rows = []
    for _, r in df.iterrows():
        row: dict = {"est_upload_id": est_id, "data_referencia": data_ref_str}
        for c in campos:
            val = r.get(c)
            if val is not None and str(val) not in ("nan", "None", ""):
                row[c] = val
        rows.append(row)

    batch_size = 500
    for i in range(0, len(rows), batch_size):
        db.table("estoque_itens").insert(rows[i:i + batch_size]).execute()

    atualizar_status_upload(upload_id, "concluido", total_registros=len(rows), registros_processados=len(rows))
    return {"ok": True, "mensagem": f"{len(rows)} itens de estoque importados.", "upload_id": upload_id}


async def _salvar_meta_vendedor(db, upload_id: str, df: pd.DataFrame,
                                data_ref: Optional[date], substituir: bool) -> dict:
    data_ref_str = str(data_ref or date.today())
    existing = db.table("meta_vendedor_uploads").select("id").eq("data_referencia", data_ref_str).execute()
    if existing.data:
        if not substituir:
            return {"ok": False, "mensagem": f"Já existe Meta Vendedor para {data_ref_str}.", "ja_existe": True}
        for old in existing.data:
            db.table("meta_vendedor_itens").delete().eq("meta_upload_id", old["id"]).execute()
            db.table("meta_vendedor_uploads").delete().eq("id", old["id"]).execute()

    mu = db.table("meta_vendedor_uploads").insert({
        "upload_id": upload_id, "data_referencia": data_ref_str,
    }).execute()
    mu_id = mu.data[0]["id"]

    # "Antonio Trielo Ba" é o mesmo que "Antonio" no mapa de vendas
    VENDOR_ALIASES = {
        "antonio trielo ba": "Antonio Trielo Ba",
    }

    campos = ["vendedor", "meta_rs", "venda_rs", "tendencia_rs", "pct_tendencia_rs",
              "meta_kg", "venda_kg", "tendencia_kg", "pct_tendencia_kg", "pct_positivacao"]
    rows = []
    for _, r in df.iterrows():
        row: dict = {"meta_upload_id": mu_id, "data_referencia": data_ref_str}
        for c in campos:
            val = r.get(c)
            if val is None or str(val).strip() in ("nan", "None", "", "-"):
                continue
            row[c] = val
        vendedor = str(row.get("vendedor", "")).strip()
        if not vendedor:
            continue
        # Normaliza alias
        row["vendedor"] = VENDOR_ALIASES.get(vendedor.lower(), vendedor)
        rows.append(row)

    batch_size = 500
    for i in range(0, len(rows), batch_size):
        db.table("meta_vendedor_itens").insert(rows[i:i + batch_size]).execute()

    atualizar_status_upload(upload_id, "concluido", total_registros=len(rows), registros_processados=len(rows))
    return {"ok": True, "mensagem": f"{len(rows)} vendedores com meta importados.", "upload_id": upload_id}


async def _salvar_dde(db, upload_id: str, df: pd.DataFrame,
                       data_ref: Optional[date], substituir: bool) -> dict:
    data_ref_str = str(data_ref or date.today())
    existing = db.table("dde_uploads").select("id").eq("data_referencia", data_ref_str).execute()
    if existing.data:
        if not substituir:
            return {"ok": False, "mensagem": f"Já existe DDE para {data_ref_str}.", "ja_existe": True}
        for old in existing.data:
            db.table("dde_itens").delete().eq("dde_upload_id", old["id"]).execute()
            db.table("dde_uploads").delete().eq("id", old["id"]).execute()

    dde = db.table("dde_uploads").insert({
        "upload_id": upload_id, "data_referencia": data_ref_str,
    }).execute()
    dde_id = dde.data[0]["id"]

    campos = ["categoria", "meta_kg", "venda_kg", "estoque_kg", "custo_unitario",
              "estoque_pc", "perc_av", "ressuprimento", "dias_esperado", "dias_estoque",
              "excesso_rs", "excesso_kg", "ruptura_kg", "perc_resultado"]
    rows = []
    for _, r in df.iterrows():
        row: dict = {"dde_upload_id": dde_id, "data_referencia": data_ref_str}
        for c in campos:
            val = r.get(c)
            if val is not None and str(val) not in ("nan", "None", ""):
                row[c] = val
        cat = str(row.get("categoria", "")).strip()
        if cat and cat not in ("nan", "None", "Totais"):
            rows.append(row)

    batch_size = 500
    for i in range(0, len(rows), batch_size):
        db.table("dde_itens").insert(rows[i:i + batch_size]).execute()

    atualizar_status_upload(upload_id, "concluido", total_registros=len(rows), registros_processados=len(rows))
    return {"ok": True, "mensagem": f"{len(rows)} categorias DDE importadas.", "upload_id": upload_id}


# ─── Salvar FIXAS ─────────────────────────────────────────────────────────────

async def _salvar_produtos(db, upload_id: str, df: pd.DataFrame, tipo: str,
                            data_ref: Optional[date]) -> dict:
    db.table("produto_base_versions").update(
        {"ativo": False, "periodo_fim_vigencia": str(data_ref)}
    ).eq("ativo", True).execute()

    version = db.table("produto_base_versions").insert({
        "upload_id": upload_id,
        "tipo_base": tipo,
        "data_upload": str(data_ref or date.today()),
        "periodo_inicio_vigencia": str(data_ref or date.today()),
        "ativo": True,
    }).execute()
    version_id = version.data[0]["id"]

    campos = ["codigo", "descricao", "unidade", "categoria", "familia", "grupo_produto",
              "tipo", "fator_conversao", "peso_liquido", "peso_bruto", "cod_categoria", "cod_familia"]
    rows = []
    for _, r in df.iterrows():
        row: dict = {"version_id": version_id}
        for c in campos:
            val = r.get(c)
            if val is not None and str(val) not in ("nan", "None", ""):
                row[c] = val
        if row.get("codigo"):
            rows.append(row)

    batch_size = 500
    for i in range(0, len(rows), batch_size):
        db.table("produtos").insert(rows[i:i + batch_size]).execute()

    atualizar_status_upload(upload_id, "concluido", total_registros=len(rows),
                            registros_processados=len(rows), data_referencia=str(data_ref))
    return {"ok": True, "mensagem": f"{len(rows)} produtos importados.", "upload_id": upload_id}


async def _salvar_clientes(db, upload_id: str, df: pd.DataFrame, tipo: str,
                            data_ref: Optional[date]) -> dict:
    db.table("cliente_base_versions").update(
        {"ativo": False, "periodo_fim_vigencia": str(data_ref)}
    ).eq("ativo", True).execute()

    version = db.table("cliente_base_versions").insert({
        "upload_id": upload_id,
        "tipo_base": tipo,
        "data_upload": str(data_ref or date.today()),
        "periodo_inicio_vigencia": str(data_ref or date.today()),
        "ativo": True,
    }).execute()
    version_id = version.data[0]["id"]

    campos = ["codigo", "loja", "nome", "nome_fantasia", "estado", "municipio",
              "vendedor", "grupo_vendas", "regiao", "tabela_preco", "desconto", "rota", "rede",
              "tipo", "bloqueado"]

    def _parse_bool(val) -> bool | None:
        if val is None or str(val).strip() in ("nan", "None", ""):
            return None
        s = str(val).strip().lower()
        if s in ("inativo", "bloqueado", "sim", "true", "1", "s"):
            return True
        return False

    rows = []
    for _, r in df.iterrows():
        row: dict = {"version_id": version_id}
        for c in campos:
            val = r.get(c)
            if val is not None and str(val) not in ("nan", "None", ""):
                row[c] = _parse_bool(val) if c == "bloqueado" else val
        if row.get("codigo"):
            rows.append(row)

    batch_size = 500
    for i in range(0, len(rows), batch_size):
        db.table("clientes").insert(rows[i:i + batch_size]).execute()

    atualizar_status_upload(upload_id, "concluido", total_registros=len(rows),
                            registros_processados=len(rows), data_referencia=str(data_ref))
    return {"ok": True, "mensagem": f"{len(rows)} clientes importados.", "upload_id": upload_id}


async def _salvar_base_categorias(db, upload_id: str, df: pd.DataFrame,
                                   data_ref: Optional[date]) -> dict:
    # Substitui todos os dados (FIXA)
    db.table("base_categorias").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

    campos = ["codigo", "categoria", "produto_codigo", "familia", "grupo_produto"]
    rows = []
    for _, r in df.iterrows():
        row: dict = {"upload_id": upload_id}
        for c in campos:
            val = r.get(c)
            if val is not None and str(val) not in ("nan", "None", ""):
                row[c] = val
        if row.get("produto_codigo"):
            rows.append(row)

    batch_size = 500
    for i in range(0, len(rows), batch_size):
        db.table("base_categorias").insert(rows[i:i + batch_size]).execute()

    atualizar_status_upload(upload_id, "concluido", total_registros=len(rows),
                            registros_processados=len(rows), data_referencia=str(data_ref))
    return {"ok": True, "mensagem": f"{len(rows)} categorias importadas.", "upload_id": upload_id}


async def _salvar_tipos_tabela_preco(db, upload_id: str, df: pd.DataFrame,
                                      data_ref: Optional[date]) -> dict:
    db.table("dim_tipos_tabela_preco").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

    campos = ["filial", "cod_tabela", "descricao", "data_inicial", "data_final",
              "cond_pagto", "tipo_horario", "tab_ativa", "ecommerce"]
    rows = []
    for _, r in df.iterrows():
        row: dict = {"upload_id": upload_id}
        for c in campos:
            val = r.get(c)
            if val is not None and str(val) not in ("nan", "None", ""):
                row[c] = str(val) if isinstance(val, date) else val
        if row.get("cod_tabela"):
            rows.append(row)

    batch_size = 500
    for i in range(0, len(rows), batch_size):
        db.table("dim_tipos_tabela_preco").insert(rows[i:i + batch_size]).execute()

    atualizar_status_upload(upload_id, "concluido", total_registros=len(rows),
                            registros_processados=len(rows), data_referencia=str(data_ref))
    return {"ok": True, "mensagem": f"{len(rows)} tipos de tabela importados.", "upload_id": upload_id}


async def _salvar_tabela_cliente_rota(db, upload_id: str, df: pd.DataFrame,
                                       data_ref: Optional[date]) -> dict:
    db.table("dim_tabela_cliente_rota").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

    campos = ["nome", "nome_fantasia", "estado", "vendedor", "grupo",
              "tabela_preco", "desconto", "rota", "rede"]
    rows = []
    for _, r in df.iterrows():
        row: dict = {"upload_id": upload_id}
        for c in campos:
            val = r.get(c)
            if val is not None and str(val) not in ("nan", "None", ""):
                row[c] = val
        if row.get("nome"):
            rows.append(row)

    batch_size = 500
    for i in range(0, len(rows), batch_size):
        db.table("dim_tabela_cliente_rota").insert(rows[i:i + batch_size]).execute()

    atualizar_status_upload(upload_id, "concluido", total_registros=len(rows),
                            registros_processados=len(rows), data_referencia=str(data_ref))
    return {"ok": True, "mensagem": f"{len(rows)} vínculos cliente-rota importados.", "upload_id": upload_id}


async def _salvar_tabela_fretes(db, upload_id: str, df: pd.DataFrame,
                                 data_ref: Optional[date]) -> dict:
    db.table("dim_fretes").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

    campos = ["rota", "carro", "valor_atual", "tara", "pedido_minimo", "perc_despesa"]
    rows = []
    for _, r in df.iterrows():
        row: dict = {"upload_id": upload_id}
        for c in campos:
            val = r.get(c)
            if val is not None and str(val) not in ("nan", "None", ""):
                row[c] = val
        if row.get("rota"):
            rows.append(row)

    batch_size = 500
    for i in range(0, len(rows), batch_size):
        db.table("dim_fretes").insert(rows[i:i + batch_size]).execute()

    atualizar_status_upload(upload_id, "concluido", total_registros=len(rows),
                            registros_processados=len(rows), data_referencia=str(data_ref))
    return {"ok": True, "mensagem": f"{len(rows)} rotas de frete importadas.", "upload_id": upload_id}


async def _salvar_tabela_grupo_rede(db, upload_id: str, df: pd.DataFrame,
                                     data_ref: Optional[date]) -> dict:
    db.table("dim_grupo_rede").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

    campos = ["grupo", "descricao"]
    rows = []
    for _, r in df.iterrows():
        row: dict = {"upload_id": upload_id}
        for c in campos:
            val = r.get(c)
            if val is not None and str(val) not in ("nan", "None", ""):
                row[c] = str(val)
        if row.get("grupo"):
            rows.append(row)

    batch_size = 500
    for i in range(0, len(rows), batch_size):
        db.table("dim_grupo_rede").insert(rows[i:i + batch_size]).execute()

    atualizar_status_upload(upload_id, "concluido", total_registros=len(rows),
                            registros_processados=len(rows), data_referencia=str(data_ref))
    return {"ok": True, "mensagem": f"{len(rows)} grupos de rede importados.", "upload_id": upload_id}


async def _salvar_tabela_supervisor_vendedor(db, upload_id: str, df: pd.DataFrame,
                                              data_ref: Optional[date]) -> dict:
    db.table("dim_supervisor_vendedor").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

    campos = ["codigo", "vendedor", "local", "supervisor"]
    rows = []
    for _, r in df.iterrows():
        row: dict = {"upload_id": upload_id}
        for c in campos:
            val = r.get(c)
            if val is not None and str(val) not in ("nan", "None", ""):
                row[c] = str(val)
        if row.get("vendedor"):
            rows.append(row)

    batch_size = 500
    for i in range(0, len(rows), batch_size):
        db.table("dim_supervisor_vendedor").insert(rows[i:i + batch_size]).execute()

    atualizar_status_upload(upload_id, "concluido", total_registros=len(rows),
                            registros_processados=len(rows), data_referencia=str(data_ref))
    return {"ok": True, "mensagem": f"{len(rows)} vínculos supervisor-vendedor importados.", "upload_id": upload_id}


async def _salvar_vendedores(db, upload_id: str, df: pd.DataFrame,
                              data_ref: Optional[date]) -> dict:
    db.table("dim_vendedores").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

    campos = ["codigo", "nome", "nome_reduzido", "supervisor", "gerente"]
    rows = []
    for _, r in df.iterrows():
        row: dict = {"upload_id": upload_id, "ativo": True}
        for c in campos:
            val = r.get(c)
            if val is not None and str(val) not in ("nan", "None", ""):
                row[c] = val
        if row.get("codigo"):
            rows.append(row)

    batch_size = 500
    for i in range(0, len(rows), batch_size):
        db.table("dim_vendedores").insert(rows[i:i + batch_size]).execute()

    atualizar_status_upload(upload_id, "concluido", total_registros=len(rows),
                            registros_processados=len(rows), data_referencia=str(data_ref))
    return {"ok": True, "mensagem": f"{len(rows)} vendedores importados.", "upload_id": upload_id}


# ─── Suporte ao mapa_service ──────────────────────────────────────────────────

def _buscar_produtos_vigentes(db) -> Optional[pd.DataFrame]:
    try:
        res = db.table("produto_base_versions").select("id").eq("ativo", True).execute()
        if not res.data:
            return None
        version_id = res.data[0]["id"]
        prods = db.table("produtos").select("*").eq("version_id", version_id).execute()
        return pd.DataFrame(prods.data) if prods.data else None
    except Exception:
        return None


def _buscar_clientes_vigentes(db) -> Optional[pd.DataFrame]:
    try:
        res = db.table("cliente_base_versions").select("id").eq("ativo", True).execute()
        if not res.data:
            return None
        version_id = res.data[0]["id"]
        clis = db.table("clientes").select("*").eq("version_id", version_id).execute()
        return pd.DataFrame(clis.data) if clis.data else None
    except Exception:
        return None


def _buscar_precos(db) -> Optional[pd.DataFrame]:
    try:
        res = db.table("lista_precos_itens").select("codigo,preco_venda").execute()
        return pd.DataFrame(res.data) if res.data else None
    except Exception:
        return None


def _buscar_estoque(db) -> Optional[pd.DataFrame]:
    try:
        res = db.table("estoque_itens").select("codigo,estoque_kg").order(
            "data_referencia", desc=True
        ).limit(5000).execute()
        return pd.DataFrame(res.data) if res.data else None
    except Exception:
        return None


def _buscar_params_logistica(db) -> dict:
    try:
        res = db.table("parametros_logistica").select("*").execute()
        return {r["rota"]: r for r in (res.data or [])}
    except Exception:
        return {}


def _atualizar_fato_vendas(db, df: pd.DataFrame, upload_id: str, data_ref: Optional[date]):
    if data_ref:
        db.table("fato_vendas").delete().eq("data_referencia", str(data_ref)).execute()

    campos_fato = [
        "vendedor", "gestor", "cliente_codigo",
        "rede", "rota", "estado", "tipo_saida",
        "status_desconto", "status_inteligente",
        "quantidade", "venda_bruta", "total_venda_liquida", "total_margem_bruta",
        "margem_percentual", "desconto_tabela", "divergencia_preco",
        "ruptura_prevista", "peso_total", "ocupacao_peso", "ocupacao_valor",
    ]
    rows = []
    for _, r in df.iterrows():
        row: dict = {
            "data_referencia": str(data_ref),
            "upload_id": upload_id,
            "produto_codigo": str(r.get("codigo", "")).strip(),
            "categoria": r.get("grupo"),
        }
        for c in campos_fato:
            val = r.get(c)
            if val is not None and str(val) not in ("nan", "None", ""):
                try:
                    row[c] = float(val) if isinstance(val, (int, float)) else str(val)
                except Exception:
                    row[c] = str(val)
        rows.append(row)

    batch_size = 500
    for i in range(0, len(rows), batch_size):
        db.table("fato_vendas").insert(rows[i:i + batch_size]).execute()
