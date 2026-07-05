"""
Leitura e validação de arquivos Excel para o sistema Mapa de Vendas.
"""
import io
import pandas as pd
from datetime import date
from typing import Any

# Colunas obrigatórias por tipo (nomes originais do arquivo)
REQUIRED_COLUMNS: dict[str, list[str]] = {
    "planilha_produtos":    ["Codigo", "Descricao", "Fator Conv."],
    "planilha_clientes":    ["Codigo", "Loja", "Nome"],
    "mapa_vendas":          ["PRODUTO", "PEDIDO", "Cliente", "Qtd. Vend."],
    "lista_precos":         ["Codigo", "Preco Venda"],
    "estoque":              ["Produto", "Descricao"],
    "dde":                  ["Categoria", "Meta (Kg)", "Venda (Kg)", "Estoque (Kg)"],
    "base_categorias":      ["Produto"],
    "tipos_tabela_preco":   ["Cod. Tabela", "Descricao"],
    "vendedores":              ["Codigo", "Nome"],
    "tabela_cliente_rota":        ["Nome", "Rota"],
    "tabela_fretes":              ["ROTA"],
    "tabela_grupo_rede":          ["Grupo", "Descricao"],
    "tabela_supervisor_vendedor": ["Vendedor", "Supervisor"],
    "meta_vendedor":              ["Vendedor", "Meta (R$)"],
}

# Mapeamento nome-original → nome-normalizado
COLUMN_ALIASES: dict[str, dict[str, str]] = {
    "planilha_produtos": {
        "Grupo":        "grupo",
        "Codigo":       "codigo",
        "Descricao":    "descricao",
        "Tipo":         "tipo",
        "Unidade":      "unidade",
        "Fator Conv.":  "fator_conversao",
        "Tipo de Conv": "tipo_conversao",
        "Peso Liquido": "peso_liquido",
        "Peso Bruto":   "peso_bruto",
        "Fabricante":   "fabricante",
        "Marca":        "marca",
        "Qtd Cx Palet": "qtd_cx_palet",
        "Cod.Categori": "cod_categoria",
        "Cod.Familia":  "cod_familia",
    },
    "planilha_clientes": {
        "Codigo":      "codigo",
        "Loja":        "loja",
        "Nome":        "nome",
        "N Fantasia":  "nome_fantasia",
        "Estado":      "estado",
        "Municipio":   "municipio",
        "Vendedor":    "vendedor",
        "Bloqueado":   "bloqueado",
        "Tipo":        "tipo",
    },
    "mapa_vendas": {
        "GRUPO":       "grupo",
        "DESCRG":      "descr_grupo",
        "PRODUTO":     "codigo",
        "DESCR":       "descricao",
        "UMVEN":       "unidade",
        "PEDIDO":      "pedido",
        "Cliente":     "cliente_nome",
        "Dt Emissao":  "data_emissao",
        "Dt Saida":    "data_saida",
        "Dt Entrega":  "data_entrega",
        "Qtd. Vend.":  "quantidade",
        "Prc. Vend.":  "preco_cx",
    },
    "lista_precos": {
        "Cod. Tabela":  "cod_tabela",
        "Codigo":       "codigo",
        "Descricao":    "descricao",
        "Unidade":      "unidade",
        "Preco Base":   "preco_base",
        "Preco Venda":  "preco_venda",
        "Vlr.Desconto": "vlr_desconto",
        "Data Inicial": "data_inicial",
        "Data Final":   "data_final",
        "Estado":       "estado",
        "Tipo Operac.": "tipo_operacao",
    },
    "estoque": {
        "Ult. Preco":       "ult_preco",
        "Filial":           "filial",
        "Produto":          "codigo",
        "C Unitario":       "custo_unitario",
        "Descricao":        "descricao",
        "Unidade":          "unidade",
        "Armz":             "armz",
        "Saldo Atual":      "estoque_kg",
        "Vlr. em Estoque":  "valor_estoque",
        "Nome Empresa":     "nome_empresa",
        "Nome Filial":      "nome_filial",
    },
    "dde": {
        "Categoria":       "categoria",
        "Meta (Kg)":       "meta_kg",
        "Venda (Kg)":      "venda_kg",
        "Estoque (Kg)":    "estoque_kg",
        "Custo Unitário":  "custo_unitario",
        "Estoque (PC)":    "estoque_pc",
        "% AV":            "perc_av",
        "Ressuprimento":   "ressuprimento",
        "Dias Esperado":   "dias_esperado",
        "Dias Estoque":    "dias_estoque",
        "Excesso (R$)":    "excesso_rs",
        "Excesso (Kg)":    "excesso_kg",
        "Ruptura (Kg)":    "ruptura_kg",
        "%Resultado":      "perc_resultado",
    },
    "base_categorias": {
        "Código":        "codigo",
        "Categoria":     "categoria",
        "Produto":       "produto_codigo",
        "Família":       "familia",
        "Grupo Produto": "grupo_produto",
    },
    "tipos_tabela_preco": {
        "Filial":       "filial",
        "Cod. Tabela":  "cod_tabela",
        "Descricao":    "descricao",
        "Data Inicial": "data_inicial",
        "Data Final":   "data_final",
        "Cond.Pagto.":  "cond_pagto",
        "Tipo horario": "tipo_horario",
        "Tab. Ativa":   "tab_ativa",
        "E-Commerce":   "ecommerce",
    },
    "vendedores": {
        "Codigo":       "codigo",
        "Nome":         "nome",
        "Nome Reduzid": "nome_reduzido",
        "Supervisor":   "supervisor",
        "Gerente":      "gerente",
    },
    "tabela_cliente_rota": {
        "Nome":            "nome",
        "N Fantasia":      "nome_fantasia",
        "Estado":          "estado",
        "Vendedor":        "vendedor",
        "Grupo":           "grupo",
        "Tabela de Preço": "tabela_preco",
        "Desc.":           "desconto",
        "Rota":            "rota",
        "Rede":            "rede",
    },
    "tabela_fretes": {
        "ROTA":          "rota",
        "CARRO":         "carro",
        "ATUAL":         "valor_atual",
        "TARA":          "tara",
        "PEDIDO MINIMO": "pedido_minimo",
        "% DESPESA":     "perc_despesa",
    },
    "tabela_grupo_rede": {
        "Grupo":     "grupo",
        "Descricao": "descricao",
    },
    "tabela_supervisor_vendedor": {
        "Código":     "codigo",
        "Vendedor":   "vendedor",
        "Local":      "local",
        "Supervisor": "supervisor",
    },
    "meta_vendedor": {
        "Vendedor":          "vendedor",
        "Meta (R$)":         "meta_rs",
        "Venda (R$)":        "venda_rs",
        "Tendência (R$)":    "tendencia_rs",
        "%Tendência (R$)":   "pct_tendencia_rs",
        "Meta (Kg)":         "meta_kg",
        "Venda (Kg)":        "venda_kg",
        "Tendência (Kg)":    "tendencia_kg",
        "%Tendência (Kg)":   "pct_tendencia_kg",
        "%Positivação":      "pct_positivacao",
    },
}


def read_excel_file(content: bytes, tipo: str) -> tuple[pd.DataFrame, list[str]]:
    """Lê o arquivo Excel e retorna DataFrame normalizado e lista de avisos."""
    avisos: list[str] = []
    try:
        sheet_name = _get_sheet_name(tipo)
        df = pd.read_excel(
            io.BytesIO(content),
            sheet_name=sheet_name,
            dtype=str,
            header=_get_header_row(tipo),
        )
    except Exception as e:
        raise ValueError(f"Erro ao ler arquivo Excel: {e}")

    df = _clean_dataframe(df, tipo, avisos)
    return df, avisos


def _get_sheet_name(tipo: str) -> str | int:
    mapping = {
        "mapa_vendas":        "2-Mapa",
        "lista_precos":       "2-Produtos da tabela de preco",
        "dde":                0,
        "estoque":            0,
        "planilha_produtos":  0,
        "planilha_clientes":  "1-Clientes",
        "base_categorias":    0,
        "tipos_tabela_preco": "Listagem do Browse",
        "vendedores":           "1-Vendedores",
        "tabela_cliente_rota":        "Planilha1",
        "tabela_fretes":              "Planilha1",
        "tabela_grupo_rede":          "Planilha2",
        "tabela_supervisor_vendedor": "Planilha1",
        "meta_vendedor":              "Sheet1",
    }
    return mapping.get(tipo, 0)


def _get_header_row(tipo: str) -> int:
    # Mapa de Vendas: linha 0 é "Mapa" (merged header), linha 1 são os títulos reais
    if tipo == "mapa_vendas":
        return 1
    return 0


def _clean_dataframe(df: pd.DataFrame, tipo: str, _avisos: list[str]) -> pd.DataFrame:
    df = df.dropna(how="all").reset_index(drop=True)
    df.columns = [str(c).strip() for c in df.columns]

    aliases = COLUMN_ALIASES.get(tipo, {})
    df = df.rename(columns=aliases)

    # Mapa de Vendas: remover linhas de subtotal de grupo (têm grupo mas sem código de produto)
    if tipo == "mapa_vendas" and "codigo" in df.columns:
        df = df.dropna(subset=["codigo"]).reset_index(drop=True)
        df = df[~df["codigo"].astype(str).str.strip().isin(["nan", "None", ""])].reset_index(drop=True)

    # Meta Vendedor: remover linha de Totais e linhas sem vendedor
    if tipo == "meta_vendedor" and "vendedor" in df.columns:
        df = df[df["vendedor"].notna()].reset_index(drop=True)
        df = df[~df["vendedor"].astype(str).str.strip().isin(
            ["nan", "None", "", "Totais"]
        )].reset_index(drop=True)

    numeric_cols = _get_numeric_cols(tipo)
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", ".").str.replace(" ", ""),
                errors="coerce",
            )

    date_cols = _get_date_cols(tipo)
    for col in date_cols:
        if col in df.columns:
            df[col] = df[col].apply(_parse_excel_date)

    str_cols = [c for c in df.columns if c not in numeric_cols + date_cols]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().replace("nan", None)

    return df


def _get_numeric_cols(tipo: str) -> list[str]:
    mapping: dict[str, list[str]] = {
        "planilha_produtos":  ["fator_conversao", "peso_liquido", "peso_bruto", "qtd_cx_palet"],
        "mapa_vendas":        ["quantidade", "preco_cx"],
        "lista_precos":       ["preco_base", "preco_venda", "vlr_desconto"],
        "estoque":            ["ult_preco", "custo_unitario", "estoque_kg", "valor_estoque"],
        "dde":                ["meta_kg", "venda_kg", "estoque_kg", "custo_unitario", "estoque_pc",
                               "perc_av", "ressuprimento", "dias_esperado", "dias_estoque",
                               "excesso_rs", "excesso_kg", "ruptura_kg", "perc_resultado"],
        "planilha_clientes":    ["desconto"],
        "tabela_cliente_rota":  ["desconto"],
        "tabela_fretes":        ["valor_atual", "tara", "pedido_minimo", "perc_despesa"],
        "meta_vendedor":        ["meta_rs", "venda_rs", "tendencia_rs", "pct_tendencia_rs",
                                 "meta_kg", "venda_kg", "tendencia_kg", "pct_tendencia_kg",
                                 "pct_positivacao"],
    }
    return mapping.get(tipo, [])


def _get_date_cols(tipo: str) -> list[str]:
    mapping: dict[str, list[str]] = {
        "mapa_vendas":        ["data_emissao", "data_saida", "data_entrega"],
        "lista_precos":       ["data_inicial", "data_final"],
        "tipos_tabela_preco": ["data_inicial", "data_final"],
    }
    return mapping.get(tipo, [])


def _parse_excel_date(val: Any) -> date | None:
    if val is None or str(val).strip() in ("", "nan", "None"):
        return None
    try:
        numeric = float(str(val).replace(",", "."))
        if 1000 < numeric < 100000:
            return (pd.Timestamp("1899-12-30") + pd.Timedelta(days=int(numeric))).date()
    except (ValueError, TypeError):
        pass
    try:
        # Try ISO format first (yyyy-mm-dd or yyyy-mm-dd HH:MM:SS), then BR day-first
        s = str(val).strip()
        if s[:4].isdigit() and s[4:5] == "-":
            return pd.to_datetime(s).date()
        return pd.to_datetime(s, dayfirst=True).date()
    except Exception:
        return None


def validate_columns(df: pd.DataFrame, tipo: str) -> list[str]:
    """Retorna colunas obrigatórias ausentes (nomes normalizados)."""
    aliases = COLUMN_ALIASES.get(tipo, {})
    required_normalized = [
        aliases.get(c, c) for c in REQUIRED_COLUMNS.get(tipo, [])
    ]
    missing = [c for c in required_normalized if c not in df.columns]
    return missing


def preview_data(df: pd.DataFrame, n: int = 5) -> list[dict]:
    return df.head(n).where(pd.notna(df.head(n)), None).to_dict(orient="records")


def get_column_list(df: pd.DataFrame) -> list[str]:
    return list(df.columns)
