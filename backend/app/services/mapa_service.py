"""
Motor de cálculo do Mapa de Vendas — replica a lógica da planilha Excel.
"""
import pandas as pd
import numpy as np  # type: ignore[import-untyped]
from datetime import date
from typing import Optional


# ─── Funções de cálculo unitário ────────────────────────────────────────────

def calc_venda_bruta(qtd: float, preco_cx: float) -> float:
    return round((qtd or 0) * (preco_cx or 0), 2)


def calc_venda_liquida_unit(preco_cx: float, desconto: float) -> float:
    return round((preco_cx or 0) * (1 - (desconto or 0)), 4)


def calc_total_venda_liquida(qtd: float, venda_liq: float) -> float:
    return round((qtd or 0) * (venda_liq or 0), 2)


def calc_margem_unit(venda_liq: float, custo: float) -> float:
    return round((venda_liq or 0) - (custo or 0), 4)


def calc_margem_percentual(margem_unit: float, venda_liq: float) -> float:
    if not venda_liq or venda_liq == 0:
        return 0.0
    return round(margem_unit / venda_liq, 4)


def calc_total_margem_bruta(qtd: float, margem_unit: float) -> float:
    return round((qtd or 0) * (margem_unit or 0), 2)


def calc_desconto_tabela(preco_cx: float, preco_tabela: float) -> float:
    if not preco_tabela or preco_tabela == 0:
        return 0.0
    return round(1 - (preco_cx or 0) / preco_tabela, 4)


def calc_status_desconto(preco_cx: float, preco_tabela: float) -> str:
    if preco_tabela is None or preco_tabela == 0:
        return "sem_tabela"
    diff = preco_cx - preco_tabela
    if abs(diff) < 0.001:
        return "igual_tabela"
    if diff < 0:
        return "abaixo_tabela"
    return "acima_tabela"


def calc_divergencia_preco(preco_cx: float, preco_tabela: float) -> float:
    return round((preco_cx or 0) - (preco_tabela or 0), 2)


def calc_ruptura_prevista(venda_qtd: float, estoque_kg: float, fc: float = 1.0) -> float:
    """Ruptura = venda em kg - estoque disponível (negativo = ruptura)."""
    venda_kg = (venda_qtd or 0) * (fc or 1.0)
    sobra = (estoque_kg or 0) - venda_kg
    return round(min(sobra, 0), 3)  # negativo indica ruptura


def calc_status_logistica(
    valor_rota: float,
    peso_rota: float,
    valor_minimo: float,
    tara_minima: float,
    _pedido_minimo: float,
) -> dict:
    if valor_minimo == 0 and tara_minima == 0:
        return {
            "status_valor": "sem_parametro",
            "status_peso": "sem_parametro",
            "status_inteligente": "sem_parametro",
            "ocupacao_valor": 0.0,
            "ocupacao_peso": 0.0,
        }
    status_valor = "viavel" if valor_rota >= valor_minimo else "aumentar_valor"
    status_peso = "viavel" if peso_rota >= tara_minima else "aumentar_peso"

    if status_valor == "viavel" and status_peso == "viavel":
        status_inteligente = "viavel"
    elif status_valor != "viavel":
        status_inteligente = "aumentar_valor"
    else:
        status_inteligente = "aumentar_peso"

    ocupacao_valor = round(valor_rota / valor_minimo, 4) if valor_minimo > 0 else 0.0
    ocupacao_peso = round(peso_rota / tara_minima, 4) if tara_minima > 0 else 0.0

    return {
        "status_valor": status_valor,
        "status_peso": status_peso,
        "status_inteligente": status_inteligente,
        "ocupacao_valor": ocupacao_valor,
        "ocupacao_peso": ocupacao_peso,
    }


# ─── Processamento do DataFrame do Mapa ────────────────────────────────────

def processar_mapa(
    df_mapa: pd.DataFrame,
    df_produtos: Optional[pd.DataFrame],
    df_clientes: Optional[pd.DataFrame],
    df_precos: Optional[pd.DataFrame],
    df_estoque: Optional[pd.DataFrame],
    params_logistica: dict[str, dict],
) -> pd.DataFrame:
    """
    Processa o DataFrame do Mapa de Vendas, cruza com bases e calcula todos os campos.
    Retorna DataFrame enriquecido pronto para inserção no banco.
    """
    df = df_mapa.copy()

    # Garantir tipos numéricos
    for col in ["quantidade", "preco_cx", "preco_tabela", "fc", "peso_total"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # ── Cruzar com produtos para custo e peso ──────────────────────────────
    if df_produtos is not None and "codigo" in df_produtos.columns:
        prod_lookup = df_produtos.set_index("codigo")[
            [c for c in ["custo_unitario", "peso_liquido", "fator_conversao", "categoria",
                         "familia", "grupo_produto"] if c in df_produtos.columns]
        ].to_dict("index")

        for col in ["custo_unitario", "peso_liquido"]:
            if col not in df.columns:
                df[col] = 0.0

        if "categoria" not in df.columns:
            df["categoria"] = None
        if "familia" not in df.columns:
            df["familia"] = None
        if "grupo_produto" not in df.columns:
            df["grupo_produto"] = None

        for idx, row in df.iterrows():
            cod = str(row.get("codigo", "")).strip()
            prod = prod_lookup.get(cod, {})
            for field in ["custo_unitario", "peso_liquido", "fator_conversao",
                          "categoria", "familia", "grupo_produto"]:
                if field in prod and (df.at[idx, field] == 0 or pd.isna(df.at[idx, field])):
                    df.at[idx, field] = prod[field]
    else:
        for col in ["custo_unitario", "peso_liquido"]:
            if col not in df.columns:
                df[col] = 0.0

    # ── Cruzar com clientes para desconto e rede ──────────────────────────
    if df_clientes is not None and "codigo" in df_clientes.columns:
        cli_cols = [c for c in ["desconto", "nome", "nome_fantasia", "rede", "rota",
                                 "tabela_preco"] if c in df_clientes.columns]
        cli_lookup = df_clientes.set_index("codigo")[cli_cols].to_dict("index")

        for col in ["desconto_cliente", "cliente_nome"]:
            if col not in df.columns:
                df[col] = None

        for idx, row in df.iterrows():
            cod = str(row.get("cliente_codigo", "")).strip()
            cli = cli_lookup.get(cod, {})
            if "desconto" in cli and cli["desconto"]:
                df.at[idx, "desconto_cliente"] = float(cli["desconto"]) / 100
            if "nome" in cli and not row.get("cliente_nome"):
                df.at[idx, "cliente_nome"] = cli["nome"]
            if "rede" in cli and (not row.get("rede") or str(row.get("rede")) == "nan"):
                df.at[idx, "rede"] = cli["rede"]
            if "rota" in cli and (not row.get("rota") or str(row.get("rota")) == "nan"):
                df.at[idx, "rota"] = cli["rota"]

    # ── Cruzar com preços para preco_tabela ──────────────────────────────
    if df_precos is not None and "codigo" in df_precos.columns:
        preco_lookup = (
            df_precos.groupby("codigo")["preco_venda"].max().to_dict()
        )
        for idx, row in df.iterrows():
            cod = str(row.get("codigo", "")).strip()
            if preco_lookup.get(cod) and (not row.get("preco_tabela") or row["preco_tabela"] == 0):
                df.at[idx, "preco_tabela"] = preco_lookup[cod]

    # ── Calcular desconto do cliente (se não veio do cruzamento) ─────────
    if "desconto_cliente" not in df.columns:
        df["desconto_cliente"] = 0.0
    df["desconto_cliente"] = pd.to_numeric(df["desconto_cliente"], errors="coerce").fillna(0)

    # ── Cálculos de venda e margem ──────────────────────────────────────
    df["venda_bruta"] = df.apply(
        lambda r: calc_venda_bruta(r["quantidade"], r["preco_cx"]), axis=1
    )
    df["venda_liquida_unit"] = df.apply(
        lambda r: calc_venda_liquida_unit(r["preco_cx"], r["desconto_cliente"]), axis=1
    )
    df["total_venda_liquida"] = df.apply(
        lambda r: calc_total_venda_liquida(r["quantidade"], r["venda_liquida_unit"]), axis=1
    )
    if "custo_unitario" not in df.columns:
        df["custo_unitario"] = 0.0
    df["custo_unitario"] = pd.to_numeric(df["custo_unitario"], errors="coerce").fillna(0)
    df["margem_unit"] = df.apply(
        lambda r: calc_margem_unit(r["venda_liquida_unit"], r["custo_unitario"]), axis=1
    )
    df["total_margem_bruta"] = df.apply(
        lambda r: calc_total_margem_bruta(r["quantidade"], r["margem_unit"]), axis=1
    )
    df["margem_percentual"] = df.apply(
        lambda r: calc_margem_percentual(r["margem_unit"], r["venda_liquida_unit"]), axis=1
    )

    # ── Preço de tabela e status ─────────────────────────────────────────
    if "preco_tabela" not in df.columns:
        df["preco_tabela"] = 0.0
    df["preco_tabela"] = pd.to_numeric(df["preco_tabela"], errors="coerce").fillna(0)
    df["desconto_tabela"] = df.apply(
        lambda r: calc_desconto_tabela(r["preco_cx"], r["preco_tabela"]), axis=1
    )
    df["status_desconto"] = df.apply(
        lambda r: calc_status_desconto(r["preco_cx"], r["preco_tabela"]), axis=1
    )
    df["divergencia_preco"] = df.apply(
        lambda r: calc_divergencia_preco(r["preco_cx"], r["preco_tabela"]), axis=1
    )

    # ── Ruptura prevista ──────────────────────────────────────────────────
    if df_estoque is not None and "codigo" in df_estoque.columns:
        est_lookup = df_estoque.set_index("codigo")["estoque_kg"].to_dict()
        df["ruptura_prevista"] = df.apply(
            lambda r: calc_ruptura_prevista(
                r["quantidade"],
                est_lookup.get(str(r.get("codigo", "")).strip(), 0),
                r.get("fc", 1.0) or 1.0,
            ),
            axis=1,
        )
    else:
        df["ruptura_prevista"] = 0.0

    # ── Logística por rota ────────────────────────────────────────────────
    if "rota" in df.columns and params_logistica:
        rota_groups = df.groupby("rota", dropna=False)
        valor_por_rota = rota_groups["total_venda_liquida"].transform("sum")
        peso_por_rota = rota_groups["peso_total"].transform("sum")
        df["valor_rota"] = valor_por_rota
        df["peso_rota"] = peso_por_rota

        def _logistica_row(r):
            rota = str(r.get("rota", "")).strip()
            params = params_logistica.get(rota, {})
            res = calc_status_logistica(
                r.get("valor_rota", 0),
                r.get("peso_rota", 0),
                params.get("valor_minimo", 0),
                params.get("tara_minima", 0),
                params.get("pedido_minimo", 0),
            )
            return pd.Series(res)

        logistica_df = df.apply(_logistica_row, axis=1)
        for col in logistica_df.columns:
            df[col] = logistica_df[col]
    else:
        for col in ["valor_rota", "peso_rota", "status_valor", "status_peso",
                    "status_inteligente", "ocupacao_valor", "ocupacao_peso"]:
            df[col] = None

    return df


def df_to_itens(df: pd.DataFrame, mapa_upload_id: str, data_referencia: date) -> list[dict]:
    """Converte o DataFrame processado em lista de dicts para inserção."""
    campos = [
        # Campos diretos do novo formato
        "grupo", "descr_grupo", "codigo", "descricao", "unidade", "pedido", "cliente_nome",
        "data_emissao", "data_saida", "data_entrega", "quantidade", "preco_cx",
        # Campos do formato anterior (serão None no novo formato)
        "fc", "cliente_codigo", "data_pedido", "preco_tabela", "custo_unitario",
        "vendedor", "gestor", "estado", "rede", "rota", "tipo_saida", "peso_total",
        # Campos calculados
        "venda_bruta", "venda_liquida_unit", "total_venda_liquida", "margem_unit",
        "total_margem_bruta", "margem_percentual", "desconto_tabela", "status_desconto",
        "divergencia_preco", "ruptura_prevista", "valor_rota", "peso_rota",
        "status_valor", "status_peso", "status_inteligente", "ocupacao_peso", "ocupacao_valor",
    ]
    rows = []
    for _, r in df.iterrows():
        row: dict = {
            "mapa_upload_id": mapa_upload_id,
            "data_referencia": str(data_referencia),
        }
        for campo in campos:
            val = r.get(campo)
            if pd.isna(val) if not isinstance(val, str) else False:
                val = None
            if isinstance(val, (np.integer,)):
                val = int(val)
            elif isinstance(val, (np.floating,)):
                val = float(val)
            elif isinstance(val, date):
                val = str(val)
            row[campo] = val
        rows.append(row)
    return rows
