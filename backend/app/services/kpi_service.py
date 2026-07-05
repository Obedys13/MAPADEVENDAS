"""
Serviço de KPIs — calcula indicadores a partir do mapa_vendas_itens
enriquecido em tempo real com as tabelas de referência (dim_tabela_cliente_rota,
base_categorias, dim_vendedores, estoque_itens, lista_precos_itens, dim_fretes).
"""
from datetime import date, timedelta
from typing import Optional
import pandas as pd
from ..core.database import get_service_client
from ..schemas.dashboard import (
    KpiDashboard, KpiVendas, KpiMargem, KpiMeta, KpiRuptura, KpiLogistica,
    GraficoDashboard, GraficoItem, ResumoTabela, FiltrosDashboard,
)


# ─── Carregamento ────────────────────────────────────────────────────────────

def _load_mapa(db, filtros: FiltrosDashboard) -> tuple[pd.DataFrame, Optional[str]]:
    """Carrega mapa_vendas_itens do período. Retorna (df, data_ultimo_upload)."""
    q = db.table("mapa_vendas_uploads").select("id,data_referencia")
    if filtros.data_inicio:
        q = q.gte("data_referencia", str(filtros.data_inicio))
    if filtros.data_fim:
        q = q.lte("data_referencia", str(filtros.data_fim))
    if not filtros.data_inicio and not filtros.data_fim:
        # Default: últimos 30 dias
        cutoff = str(date.today() - timedelta(days=30))
        q = q.gte("data_referencia", cutoff)

    uploads = q.order("data_referencia", desc=True).limit(90).execute().data or []
    if not uploads:
        return pd.DataFrame(), None

    ultima_data = uploads[0]["data_referencia"]
    data_refs = {u["id"]: u["data_referencia"] for u in uploads}
    upload_ids = list(data_refs.keys())

    rows: list[dict] = []
    for i in range(0, len(upload_ids), 20):
        chunk = upload_ids[i:i + 20]
        res = db.table("mapa_vendas_itens").select(
            "mapa_upload_id,grupo,descr_grupo,codigo,descricao,unidade,"
            "pedido,cliente_nome,data_emissao,quantidade,preco_cx"
        ).in_("mapa_upload_id", chunk).execute()
        rows.extend(res.data or [])

    if not rows:
        return pd.DataFrame(), ultima_data

    df = pd.DataFrame(rows)
    df["data_referencia"] = df["mapa_upload_id"].map(data_refs)
    df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce").fillna(0)
    df["preco_cx"] = pd.to_numeric(df["preco_cx"], errors="coerce").fillna(0)
    df["venda_bruta"] = df["quantidade"] * df["preco_cx"]
    df["_codigo_key"] = df["codigo"].fillna("").str.strip()
    # Normalize client key: uppercase, collapse multiple spaces
    df["_cliente_key"] = (
        df["cliente_nome"].fillna("").str.strip().str.upper()
        .str.replace(r"\s+", " ", regex=True)
    )
    # CONC key: codigo + unidade (e.g. "001.021" + "CX" = "001.021CX")
    # Matches estoque_itens.codigo which stores the full CONC value
    unidade_s = (
        df["unidade"].fillna("").str.strip().str.upper()
        if "unidade" in df.columns
        else pd.Series("", index=df.index)
    )
    df["_conc_key"] = df["_codigo_key"] + unidade_s
    return df, ultima_data


def _load_refs(db, prod_codes: list) -> dict:
    """Carrega tabelas de referência de forma eficiente."""
    refs: dict[str, pd.DataFrame] = {}

    # Tabelas pequenas — carrega tudo (< 1000 linhas cada)
    for table, key in [
        ("dim_tabela_cliente_rota", "clientes_rota"),
        ("dim_vendedores",          "vendedores"),
        ("dim_supervisor_vendedor", "supervisores"),
        ("dim_fretes",              "fretes"),
        ("dim_grupo_rede",          "grupo_rede"),
    ]:
        try:
            r = db.table(table).select("*").limit(1000).execute()
            refs[key] = pd.DataFrame(r.data or [])
        except Exception:
            refs[key] = pd.DataFrame()

    # Tabelas grandes — filtra pelos códigos do mapa (estoque usa código puro; unidade é coluna separada)
    for table, col, key in [
        ("base_categorias",    "codigo", "categorias"),
        ("estoque_itens",      "codigo", "estoque"),
        ("lista_precos_itens", "codigo", "precos"),
    ]:
        try:
            if prod_codes:
                rows: list[dict] = []
                for i in range(0, len(prod_codes), 100):
                    res = db.table(table).select("*").in_(col, prod_codes[i:i+100]).execute()
                    rows.extend(res.data or [])
                refs[key] = pd.DataFrame(rows)
            else:
                refs[key] = pd.DataFrame()
        except Exception:
            refs[key] = pd.DataFrame()

    # Descontos da planilha_clientes (versão ativa) — fonte correta para venda_liquida
    # Supabase retorna máx 1000 linhas por request; paginamos para obter todos os clientes
    try:
        vr = db.table("cliente_base_versions").select("id").eq("ativo", True)\
               .order("data_upload", desc=True).limit(1).execute()
        if vr.data:
            vid = vr.data[0]["id"]
            all_cli: list[dict] = []
            offset = 0
            while True:
                batch = db.table("clientes").select("nome_fantasia,nome,desconto")\
                          .eq("version_id", vid).range(offset, offset + 999).execute()
                if not batch.data:
                    break
                all_cli.extend(batch.data)
                if len(batch.data) < 1000:
                    break
                offset += 1000
            refs["clientes_desconto"] = pd.DataFrame(all_cli)
        else:
            refs["clientes_desconto"] = pd.DataFrame()
    except Exception:
        refs["clientes_desconto"] = pd.DataFrame()

    return refs


# ─── Enriquecimento ──────────────────────────────────────────────────────────

def _enrich(df: pd.DataFrame, refs: dict) -> pd.DataFrame:
    """Enriquece o DataFrame do mapa com dados das tabelas de referência."""
    if df.empty:
        return df

    # 1. Clientes → vendedor_code, rota, rede, desconto
    df_cli = refs.get("clientes_rota", pd.DataFrame())
    df["vendedor_code"] = ""
    df["rota"] = ""
    df["rede"] = ""
    df["desconto"] = 0.0
    if not df_cli.empty and "nome" in df_cli.columns:
        df_cli = df_cli.copy()
        # Same normalization as _load_mapa: uppercase + collapse spaces
        df_cli["_k"] = (
            df_cli["nome"].fillna("").str.strip().str.upper()
            .str.replace(r"\s+", " ", regex=True)
        )
        cli_idx = df_cli.drop_duplicates("_k").set_index("_k")
        for col, dest in [("vendedor", "vendedor_code"), ("rota", "rota"), ("rede", "rede")]:
            if col in cli_idx.columns:
                df[dest] = df["_cliente_key"].map(cli_idx[col]).fillna("")
        if "desconto" in cli_idx.columns:
            df["desconto"] = pd.to_numeric(
                df["_cliente_key"].map(cli_idx["desconto"]), errors="coerce"
            ).fillna(0).clip(upper=0.99)

        # Brand-prefix fallback for unmatched clients
        unmatched_mask = df["vendedor_code"] == ""
        if unmatched_mask.any() and not df_cli.empty:
            df_cli2 = df_cli.copy()
            df_cli2["_brand"] = df_cli2["_k"].str.replace(r"[\s\-].*", "", regex=True)
            brand_groups: dict = {}
            for brand, grp in df_cli2.groupby("_brand"):
                if not brand:
                    continue
                entry: dict = {}
                # rede: use most common value (brands → single rede network)
                if "rede" in grp.columns:
                    mode_v = grp["rede"].dropna().mode()
                    entry["rede"] = mode_v.iloc[0] if not mode_v.empty else ""
                # vendedor/rota: only assign if unique across all brand branches
                for col in ["vendedor", "rota"]:
                    if col in grp.columns:
                        vals = [v for v in grp[col].dropna().unique() if str(v).strip()]
                        entry[col] = vals[0] if len(vals) == 1 else ""
                if "desconto" in grp.columns:
                    entry["desconto"] = pd.to_numeric(grp["desconto"], errors="coerce").mean()
                brand_groups[brand] = entry
            for idx in df[unmatched_mask].index:
                key = df.at[idx, "_cliente_key"]
                brand = str(key).split()[0] if key else ""
                entry = brand_groups.get(brand, {})
                if entry.get("rede"):
                    df.at[idx, "rede"] = entry["rede"]
                if entry.get("vendedor"):
                    df.at[idx, "vendedor_code"] = entry["vendedor"]
                if entry.get("rota"):
                    df.at[idx, "rota"] = entry["rota"]
                if "desconto" in entry and pd.notna(entry["desconto"]):
                    df.at[idx, "desconto"] = float(entry["desconto"])

    # 1c. Override desconto com planilha_clientes apenas quando o valor for > 0
    # planilha_clientes.desconto = 0 para a maioria dos clientes (campo não preenchido)
    # → só sobrescreve dim_tabela_cliente_rota.desconto se vier um valor explicitamente positivo
    df_cli_desc = refs.get("clientes_desconto", pd.DataFrame())
    if not df_cli_desc.empty and "desconto" in df_cli_desc.columns:
        df_cli_desc = df_cli_desc.copy()
        if "nome_fantasia" in df_cli_desc.columns:
            df_cli_desc["_k"] = (
                df_cli_desc["nome_fantasia"].fillna("").str.strip().str.upper()
                .str.replace(r"\s+", " ", regex=True)
            )
            desc_idx = df_cli_desc.drop_duplicates("_k").set_index("_k")["desconto"]
            desconto_fantasia = pd.to_numeric(
                df["_cliente_key"].map(desc_idx), errors="coerce"
            ).clip(upper=0.99)
            # Só aplica override quando desconto > 0 (evita sobrescrever com zeros)
            has_real_discount = desconto_fantasia.notna() & (desconto_fantasia > 0)
            df["desconto"] = desconto_fantasia.where(has_real_discount, df["desconto"])

    # 1b. Rede fallback via dim_grupo_rede: client.grupo → grupo_rede.descricao
    # Only for rows that still have empty rede after exact/brand matching
    df_gr = refs.get("grupo_rede", pd.DataFrame())
    no_rede_mask = (df["rede"].fillna("") == "") | (df["rede"].str.strip().str.lower() == "sem rede")
    if not df_gr.empty and "grupo" in df_gr.columns and "descricao" in df_gr.columns and no_rede_mask.any():
        df_gr2 = df_gr.copy()
        df_gr2["_k"] = df_gr2["grupo"].fillna("").str.strip()
        gr_idx = df_gr2.drop_duplicates("_k").set_index("_k")
        # Map client.grupo from cli_idx if available
        if not df_cli.empty and "grupo" in df_cli.columns:
            cliente_grupo = df["_cliente_key"].map(
                df_cli.drop_duplicates("_k").set_index("_k")["grupo"]
            ).fillna("")
            rede_from_grupo = cliente_grupo.map(gr_idx["descricao"]).fillna("")
            df.loc[no_rede_mask, "rede"] = rede_from_grupo[no_rede_mask].where(
                rede_from_grupo[no_rede_mask] != "", df.loc[no_rede_mask, "rede"]
            )

    # 2. Vendedores → nome, supervisor, gerente
    df_vend = refs.get("vendedores", pd.DataFrame())
    df["vendedor_nome"] = df["vendedor_code"]
    df["supervisor"] = ""
    df["gerente"] = ""
    if not df_vend.empty and "codigo" in df_vend.columns:
        df_vend = df_vend.copy()
        df_vend["_k"] = df_vend["codigo"].fillna("").str.strip()
        vend_idx = df_vend.drop_duplicates("_k").set_index("_k")
        nome_col = "nome_reduzido" if "nome_reduzido" in vend_idx.columns else "nome"
        if nome_col in vend_idx.columns:
            mapped = df["vendedor_code"].map(vend_idx[nome_col]).fillna("")
            df["vendedor_nome"] = mapped.where(mapped != "", df["vendedor_code"])
        # Gerente from dim_vendedores (trustworthy)
        if "gerente" in vend_idx.columns:
            df["gerente"] = df["vendedor_code"].map(vend_idx["gerente"]).fillna("")
    # Supervisor: dim_supervisor_vendedor takes priority (has proper names like "Gestor AL")
    # dim_vendedores.supervisor may hold numeric codes — only use as last resort
    df_sup = refs.get("supervisores", pd.DataFrame())
    if not df_sup.empty and "codigo" in df_sup.columns and "supervisor" in df_sup.columns:
        df_sup = df_sup.copy()
        df_sup["_k"] = df_sup["codigo"].fillna("").str.strip()
        sup_idx = df_sup.drop_duplicates("_k").set_index("_k")
        df["supervisor"] = df["vendedor_code"].map(sup_idx["supervisor"]).fillna("")
    # Fallback to dim_vendedores.supervisor only when still empty
    if not df_vend.empty and "supervisor" in df_vend.columns:
        vend_idx2 = df_vend.copy()
        vend_idx2["_k"] = vend_idx2["codigo"].fillna("").str.strip()
        vend_idx2 = vend_idx2.drop_duplicates("_k").set_index("_k")
        sup_fallback = df["vendedor_code"].map(vend_idx2["supervisor"]).fillna("")
        df["supervisor"] = df["supervisor"].where(df["supervisor"] != "", sup_fallback)
    df["vendedor_nome"] = (
        df["vendedor_nome"].where(df["vendedor_nome"].fillna("") != "", df["vendedor_code"])
        .replace("", "Sem vínculo")
        .fillna("Sem vínculo")
    )

    # 3. Categorias (base_categorias.codigo → produto_codigo no mapa)
    df_cat = refs.get("categorias", pd.DataFrame())
    # Default: usar descr_grupo do mapa como categoria
    df["categoria"] = df.get("descr_grupo", pd.Series("", index=df.index)).fillna("").where(
        df.get("descr_grupo", pd.Series("", index=df.index)).fillna("") != "",
        df.get("grupo", pd.Series("", index=df.index)).fillna("")
    )
    df["familia"] = df["categoria"]
    df["grupo_produto"] = ""
    if not df_cat.empty and "codigo" in df_cat.columns:
        df_cat = df_cat.copy()
        df_cat["_k"] = df_cat["codigo"].fillna("").str.strip()
        # If codigo empty, try extracting from produto_codigo
        if "produto_codigo" in df_cat.columns:
            mask = df_cat["_k"] == ""
            df_cat.loc[mask, "_k"] = (
                df_cat.loc[mask, "produto_codigo"].fillna("").str.split(" - ").str[0].str.strip()
            )
        cat_idx = df_cat.drop_duplicates("_k").set_index("_k")
        for col in ["categoria", "familia", "grupo_produto"]:
            if col in cat_idx.columns:
                mapped = df["_codigo_key"].map(cat_idx[col]).fillna("")
                if col == "categoria":
                    df["categoria"] = mapped.where(mapped != "", df["categoria"])
                else:
                    df[col] = mapped

    # 4. Estoque → custo_unitario, estoque_atual
    # Fórmula Excel: =Venda Líquida - PROCV(Código & FC, Tabela2[CONC:Custo], 2, 0)
    # estoque_itens: codigo="001.021", unidade="CX" → CONC="001.021CX" (construído aqui)
    # mapa._conc_key já é "001.021CX" → match preciso por produto+unidade
    df_est = refs.get("estoque", pd.DataFrame())
    df["custo_unitario"] = 0.0
    df["estoque_atual"] = 0.0
    if not df_est.empty and "codigo" in df_est.columns:
        df_est = df_est.copy()
        for col in ["custo_unitario", "estoque_kg"]:
            if col in df_est.columns:
                df_est[col] = pd.to_numeric(df_est[col], errors="coerce").fillna(0)
        # Constrói CONC no estoque: codigo + unidade (ex: "001.021" + "CX" = "001.021CX")
        if "unidade" in df_est.columns:
            df_est["_conc"] = (df_est["codigo"].fillna("").str.strip() +
                               df_est["unidade"].fillna("").str.strip().str.upper())
        else:
            df_est["_conc"] = df_est["codigo"].fillna("").str.strip()
        df_est["_k_plain"] = df_est["codigo"].fillna("").str.strip()
        # Custo: indexado por CONC para match exato por produto+unidade
        est_cost = df_est.groupby("_conc")["custo_unitario"].mean()
        est_cost_plain = df_est.groupby("_k_plain")["custo_unitario"].mean()
        # Estoque: indexado por código puro (estoque total, independente de unidade)
        est_stock = df_est.groupby("_k_plain")["estoque_kg"].sum()
        # Custo: tenta CONC primeiro, fallback código puro
        conc_key = df["_conc_key"] if "_conc_key" in df.columns else df["_codigo_key"]
        df["custo_unitario"] = pd.to_numeric(
            conc_key.map(est_cost), errors="coerce"
        ).fillna(0).clip(lower=0)
        no_cost = df["custo_unitario"] == 0
        if no_cost.any():
            df.loc[no_cost, "custo_unitario"] = pd.to_numeric(
                df.loc[no_cost, "_codigo_key"].map(est_cost_plain), errors="coerce"
            ).fillna(0).clip(lower=0)
        df["estoque_atual"] = pd.to_numeric(
            df["_codigo_key"].map(est_stock), errors="coerce"
        ).fillna(0).clip(lower=0)

    # 5. Preço de tabela (lista_precos) → só para preco_tabela e divergência_preco
    # NÃO é usado como base para venda_liquida. A base é sempre preco_cx do mapa.
    df_prec = refs.get("precos", pd.DataFrame())
    df["preco_tabela"] = 0.0
    if not df_prec.empty and "codigo" in df_prec.columns and "preco_venda" in df_prec.columns:
        df_prec = df_prec.copy()
        df_prec["_k"] = df_prec["codigo"].fillna("").str.strip()
        df_prec["preco_venda"] = pd.to_numeric(df_prec["preco_venda"], errors="coerce").fillna(0)
        prec_idx = df_prec.groupby("_k")["preco_venda"].max()
        df["preco_tabela"] = pd.to_numeric(
            df["_codigo_key"].map(prec_idx), errors="coerce"
        ).fillna(0)

    # 6. Cálculos financeiros (fórmula fiel ao Excel: Mapa!R = Preço Cx × (1 - Desc.cliente))
    # venda_liquida por CX = preco_cx × (1 - desconto_cliente)
    df["venda_liquida_cx"] = df["preco_cx"] * (1.0 - df["desconto"])
    # Total Venda Líquida = quantidade × venda_liquida_cx
    df["venda_liquida"] = df["quantidade"] * df["venda_liquida_cx"]
    # Margem Bruta por CX = venda_liquida_cx - custo_unitario (Mapa!S = Venda Líq - Custo CONC)
    df["margem_bruta_cx"] = df["venda_liquida_cx"] - df["custo_unitario"]
    # Total Margem Bruta = quantidade × margem_bruta_cx
    df["margem_bruta"] = df["quantidade"] * df["margem_bruta_cx"]
    # Margem % = margem_bruta_cx / venda_liquida_cx
    df["margem_pct"] = (
        df["margem_bruta_cx"] / df["venda_liquida_cx"].replace(0.0, float("nan"))
    ).fillna(0.0)
    # Divergência de preço: mapa.preco_cx vs lista.preco_venda (só referência)
    df["divergencia_preco"] = df["preco_cx"] - df["preco_tabela"]
    df["ruptura_prevista"] = df["estoque_atual"] - df["quantidade"]  # < 0 = ruptura

    # Normalize empty strings to display labels
    for col, label in [("supervisor", "Sem info"), ("rede", "Sem Rede"), ("rota", "Sem Rota"),
                        ("categoria", "Sem Categoria")]:
        if col in df.columns:
            df[col] = df[col].replace("", label).fillna(label)

    return df


def _filter_df(df: pd.DataFrame, filtros: FiltrosDashboard) -> pd.DataFrame:
    if filtros.vendedor and "vendedor_code" in df.columns:
        df = df[df["vendedor_code"].fillna("") == filtros.vendedor]
    if filtros.gestor and "supervisor" in df.columns:
        df = df[df["supervisor"].fillna("") == filtros.gestor]
    if filtros.categoria and "categoria" in df.columns:
        df = df[df["categoria"].fillna("").str.contains(filtros.categoria, case=False, na=False)]
    if filtros.rede and "rede" in df.columns:
        df = df[df["rede"].fillna("") == filtros.rede]
    if filtros.rota and "rota" in df.columns:
        df = df[df["rota"].fillna("") == filtros.rota]
    return df


def _get_enriched(filtros: FiltrosDashboard):
    """Retorna (db, df_enriquecido, ultima_data) para reuso nas funções."""
    db = get_service_client()
    df_raw, ultima_data = _load_mapa(db, filtros)
    if df_raw.empty:
        return db, pd.DataFrame(), ultima_data
    prod_codes = df_raw["_codigo_key"].dropna().unique().tolist()
    refs = _load_refs(db, prod_codes)
    df = _enrich(df_raw, refs)
    df = _filter_df(df, filtros)
    return db, df, ultima_data


# ─── Meta Vendedor ───────────────────────────────────────────────────────────

def _load_meta_kpi(db, filtros: FiltrosDashboard) -> KpiMeta:
    """Carrega meta_vendedor_itens (upload mais recente) e calcula KpiMeta."""
    try:
        # Upload mais recente
        mu = db.table("meta_vendedor_uploads").select("id,data_referencia")\
               .order("data_referencia", desc=True).limit(1).execute()
        if not mu.data:
            return KpiMeta()
        mu_id = mu.data[0]["id"]

        itens_r = db.table("meta_vendedor_itens").select(
            "vendedor,meta_rs,venda_rs,tendencia_rs,pct_tendencia_rs,"
            "meta_kg,venda_kg,tendencia_kg,pct_tendencia_kg,pct_positivacao"
        ).eq("meta_upload_id", mu_id).execute()

        df = pd.DataFrame(itens_r.data or [])
        if df.empty:
            return KpiMeta()

        # Remove vendedores excluídos dos totais de meta
        EXCLUIR_META = {"antonio trielo pe"}
        df = df[~df["vendedor"].fillna("").str.strip().str.lower().isin(EXCLUIR_META)]

        # Converte numérico
        num_cols = ["meta_rs", "venda_rs", "tendencia_rs", "pct_tendencia_rs",
                    "meta_kg", "venda_kg", "tendencia_kg", "pct_tendencia_kg", "pct_positivacao"]
        for c in num_cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

        # Filtro por vendedor (correspondência parcial case-insensitive)
        if filtros.vendedor:
            filt = filtros.vendedor.strip().lower()
            mask = df["vendedor"].fillna("").str.lower().str.contains(filt, na=False)
            if mask.any():
                df = df[mask]

        meta_total   = float(df["meta_rs"].sum())
        venda_acum   = float(df["venda_rs"].sum())
        tendencia_rs = float(df["tendencia_rs"].sum())
        meta_kg      = float(df["meta_kg"].sum())
        venda_kg     = float(df["venda_kg"].sum())
        tendencia_kg = float(df["tendencia_kg"].sum())

        if meta_total <= 0:
            return KpiMeta()

        meta_115       = meta_total * 1.15
        atingimento_pct = (venda_acum / meta_total) * 100
        saldo_meta     = meta_total - venda_acum
        tend_rs_pct    = (tendencia_rs / meta_total) * 100 if meta_total > 0 else 0.0
        tend_kg_pct    = (tendencia_kg / meta_kg) * 100 if meta_kg > 0 else 0.0

        if tend_rs_pct >= 100:
            status = "acima"
        elif tend_rs_pct >= 85:
            status = "no_prazo"
        else:
            status = "abaixo"

        return KpiMeta(
            meta_mensal=round(meta_total, 2),
            meta_115=round(meta_115, 2),
            realizado_acumulado=round(venda_acum, 2),
            atingimento_percentual=round(atingimento_pct, 2),
            saldo_meta=round(saldo_meta, 2),
            status_meta=status,
            atingimento_115_percentual=round(tend_rs_pct, 2),
            venda_realizada=round(venda_acum, 2),
            tendencia_rs_pct=round(tend_rs_pct, 2),
            tonelagem_realizada=round(venda_kg / 1000, 3),
            tendencia_kg_pct=round(tend_kg_pct, 2),
        )
    except Exception:
        return KpiMeta()


# ─── KPIs ────────────────────────────────────────────────────────────────────

def get_kpis(filtros: FiltrosDashboard) -> KpiDashboard:
    db, df, ultima_data = _get_enriched(filtros)

    if df.empty:
        return KpiDashboard(
            data_referencia=filtros.data_fim, data_ultimo_upload=ultima_data,
            vendas=KpiVendas(), margem=KpiMargem(), meta=_load_meta_kpi(db, filtros),
            ruptura=KpiRuptura(), logistica=KpiLogistica(),
        )

    fat_bruto = float(df["venda_bruta"].sum())
    fat_liq = float(df["venda_liquida"].sum())
    qtd_vendida = float(df["quantidade"].sum())
    clientes_unicos = int(df["cliente_nome"].nunique()) if "cliente_nome" in df.columns else 0
    prods_unicos = int(df["_codigo_key"].nunique())
    pedidos_unicos = int(df["pedido"].nunique()) if "pedido" in df.columns else len(df)
    ticket_medio = fat_bruto / clientes_unicos if clientes_unicos > 0 else 0.0
    preco_medio = fat_bruto / qtd_vendida if qtd_vendida > 0 else 0.0

    margem_rs = float(df["margem_bruta"].sum())
    margem_pct = margem_rs / fat_liq if fat_liq > 0 else 0.0
    desconto_total = fat_bruto - fat_liq
    desconto_pct = desconto_total / fat_bruto if fat_bruto > 0 else 0.0

    df_rupt = df[df["ruptura_prevista"] < 0]
    total_ruptura = float(abs(df_rupt["ruptura_prevista"].sum()))
    qtd_prods_rupt = int(df_rupt["_codigo_key"].nunique())
    qtd_cats_rupt = int(df_rupt["categoria"].nunique()) if "categoria" in df_rupt.columns else 0

    # Produtos sem venda com estoque (usando todos os dados de estoque carregados)
    prod_codes = df["_codigo_key"].dropna().unique().tolist()
    refs_est = _load_refs(db, prod_codes)
    df_est_full = refs_est.get("estoque", pd.DataFrame())
    prods_com_venda = set(df["_codigo_key"].unique())
    prods_sem_venda_com_est = 0
    if not df_est_full.empty and "codigo" in df_est_full.columns and "estoque_kg" in df_est_full.columns:
        df_est_full["estoque_kg"] = pd.to_numeric(df_est_full["estoque_kg"], errors="coerce").fillna(0)
        prods_com_est = set(df_est_full[df_est_full["estoque_kg"] > 0]["codigo"].str.strip().unique())
        prods_sem_venda_com_est = len(prods_com_est - prods_com_venda)

    # Logística por rota
    pedidos_viaveis = pedidos_aumentar_valor = pedidos_aumentar_peso = 0
    total_rotas = 0
    if "rota" in df.columns and df["rota"].fillna("").ne("").any():
        total_rotas = int(df[df["rota"].fillna("") != ""]["rota"].nunique())
        refs_fr = _load_refs(db, [])
        df_fr = refs_fr.get("fretes", pd.DataFrame())
        if not df_fr.empty and "rota" in df_fr.columns:
            df_fr = df_fr.copy()
            for c in ["valor_atual", "pedido_minimo"]:
                if c in df_fr.columns:
                    df_fr[c] = pd.to_numeric(df_fr[c], errors="coerce").fillna(0)
            df_fr["_k"] = df_fr["rota"].fillna("").str.strip()
            fr_idx = df_fr.drop_duplicates("_k").set_index("_k")
            por_rota = df.groupby("rota")["venda_liquida"].sum()
            for rota, val in por_rota.items():
                rota_s = str(rota).strip()
                if rota_s in fr_idx.index:
                    val_min = float(fr_idx.loc[rota_s].get("valor_atual") or 0)
                    ped_min = float(fr_idx.loc[rota_s].get("pedido_minimo") or 0)
                    thr = max(val_min, ped_min)
                    if thr <= 0 or float(val) >= thr:
                        pedidos_viaveis += 1
                    elif float(val) < val_min:
                        pedidos_aumentar_valor += 1
                    else:
                        pedidos_aumentar_peso += 1

    return KpiDashboard(
        data_referencia=filtros.data_fim,
        data_ultimo_upload=ultima_data,
        vendas=KpiVendas(
            faturamento_bruto=round(fat_bruto, 2),
            faturamento_liquido=round(fat_liq, 2),
            qtd_vendida=round(qtd_vendida, 1),
            ticket_medio=round(ticket_medio, 2),
            preco_medio=round(preco_medio, 4),
            qtd_pedidos=pedidos_unicos,
            qtd_clientes=clientes_unicos,
            qtd_produtos=prods_unicos,
        ),
        margem=KpiMargem(
            margem_bruta_rs=round(margem_rs, 2),
            margem_bruta_percentual=round(margem_pct * 100, 2),
            desconto_total=round(desconto_total, 2),
            desconto_percentual=round(desconto_pct * 100, 2),
        ),
        meta=_load_meta_kpi(db, filtros),
        ruptura=KpiRuptura(
            total_ruptura_kg=round(total_ruptura, 2),
            qtd_produtos_ruptura=qtd_prods_rupt,
            qtd_categorias_ruptura=qtd_cats_rupt,
            produtos_sem_venda_com_estoque=prods_sem_venda_com_est,
        ),
        logistica=KpiLogistica(
            pedidos_viaveis=pedidos_viaveis,
            pedidos_aumentar_valor=pedidos_aumentar_valor,
            pedidos_aumentar_peso=pedidos_aumentar_peso,
            total_rotas=total_rotas,
        ),
    )


def _top_n(df: pd.DataFrame, col: str, val: str = "venda_liquida", n: int = 10) -> list[GraficoItem]:
    if col not in df.columns:
        return []
    g = df.groupby(col)[val].sum().nlargest(n).reset_index()
    return [GraficoItem(label=str(r[col] or "Sem info"), valor=round(float(r[val]), 2)) for _, r in g.iterrows()]


def get_graficos(filtros: FiltrosDashboard) -> GraficoDashboard:
    _, df, _ = _get_enriched(filtros)
    if df.empty:
        return GraficoDashboard()

    daily = df.groupby("data_referencia").agg(
        venda=("venda_liquida", "sum"), margem=("margem_bruta", "sum")
    ).reset_index().sort_values("data_referencia")
    evolucao = [
        GraficoItem(label=str(r["data_referencia"]), valor=round(float(r["venda"]), 2),
                    secundario=round(float(r["margem"]), 2))
        for _, r in daily.iterrows()
    ]

    rupt_df = df[df["ruptura_prevista"] < 0].copy()
    rupt_df["rupt_abs"] = abs(rupt_df["ruptura_prevista"])
    rupturas_cat = _top_n(rupt_df, "categoria", "rupt_abs") if not rupt_df.empty else []

    div_df = df[df["preco_tabela"] > 0].copy()
    div_df["div_abs"] = div_df["divergencia_preco"].abs()
    divs = _top_n(div_df, "descricao", "div_abs") if not div_df.empty else []

    return GraficoDashboard(
        top10_categorias=_top_n(df, "categoria"),
        top10_produtos=_top_n(df, "descricao"),
        por_vendedor=_top_n(df, "vendedor_nome", n=20),
        por_gestor=_top_n(df, "supervisor", n=10),
        por_rede=_top_n(df, "rede"),
        por_rota=_top_n(df, "rota"),
        evolucao_diaria=evolucao,
        maiores_rupturas_categoria=rupturas_cat,
        divergencias_preco=divs,
    )


def get_resumo_vendedor(filtros: FiltrosDashboard) -> list[ResumoTabela]:
    _, df, _ = _get_enriched(filtros)
    if df.empty or "vendedor_nome" not in df.columns:
        return []

    g = df.groupby("vendedor_nome", dropna=False).agg(
        venda_bruta=("venda_bruta", "sum"),
        venda_liquida=("venda_liquida", "sum"),
        margem_rs=("margem_bruta", "sum"),
        qtd=("quantidade", "sum"),
        pedidos=("pedido", "nunique"),
    ).reset_index().sort_values("venda_liquida", ascending=False)

    result = []
    for _, r in g.iterrows():
        ml = float(r["venda_liquida"])
        result.append(ResumoTabela(
            nome=str(r["vendedor_nome"] or "Sem vínculo"),
            venda_bruta=round(float(r["venda_bruta"]), 2),
            venda_liquida=round(ml, 2),
            margem_rs=round(float(r["margem_rs"]), 2),
            margem_percentual=round(float(r["margem_rs"]) / ml * 100, 2) if ml > 0 else 0.0,
            quantidade=round(float(r["qtd"]), 1),
            qtd_pedidos=int(r["pedidos"]),
        ))
    return result


def gerar_insights(filtros: FiltrosDashboard) -> list[str]:
    _, df, _ = _get_enriched(filtros)
    if df.empty:
        return ["Nenhum dado encontrado para o período selecionado."]

    insights: list[str] = []
    fat_liq = float(df["venda_liquida"].sum())
    fat_bruto = float(df["venda_bruta"].sum())

    if "categoria" in df.columns and df["categoria"].fillna("").ne("").any():
        cat_s = df.groupby("categoria")["venda_liquida"].sum()
        top_cat = cat_s.idxmax()
        pct = round(cat_s.max() / fat_liq * 100, 1) if fat_liq > 0 else 0
        insights.append(f"Categoria líder: '{top_cat}' representa {pct}% da venda líquida.")

    prod_s = df.groupby("descricao")["venda_liquida"].sum()
    top_prod = prod_s.idxmax()
    insights.append(f"Produto mais vendido: '{top_prod}' — R$ {prod_s.max():,.0f}.")

    if "vendedor_nome" in df.columns:
        df_vend = df[df["vendedor_nome"].fillna("") != "Sem vínculo"]
        if not df_vend.empty:
            vend_s = df_vend.groupby("vendedor_nome")["venda_liquida"].sum()
            top_vend = vend_s.idxmax()
            insights.append(f"Vendedor destaque: {top_vend} — R$ {vend_s.max():,.0f}.")

    margem_total = float(df["margem_bruta"].sum())
    if fat_liq > 0:
        insights.append(f"Margem bruta: {margem_total / fat_liq * 100:.1f}% (R$ {margem_total:,.0f}).")

    if fat_bruto > 0 and (fat_bruto - fat_liq) > 0:
        desc_pct = (fat_bruto - fat_liq) / fat_bruto * 100
        insights.append(f"Desconto médio aplicado: {desc_pct:.1f}% (R$ {fat_bruto - fat_liq:,.0f}).")

    if "ruptura_prevista" in df.columns:
        df_rupt = df[df["ruptura_prevista"] < 0]
        if not df_rupt.empty:
            total_rup = abs(float(df_rupt["ruptura_prevista"].sum()))
            cats_rup = int(df_rupt["categoria"].nunique()) if "categoria" in df_rupt.columns else 0
            insights.append(
                f"Risco de ruptura: {df_rupt['_codigo_key'].nunique()} produto(s), "
                f"{total_rup:.1f} kg em deficit — {cats_rup} categoria(s) afetada(s)."
            )

    if "preco_tabela" in df.columns:
        df_div = df[(df["preco_tabela"] > 0) & (df["divergencia_preco"].abs() > 0.01)]
        if not df_div.empty:
            insights.append(
                f"{df_div['_codigo_key'].nunique()} produto(s) com preço diferente da tabela vigente."
            )

    return insights


# ─── Análises específicas (chamadas por analises.py) ─────────────────────────

def _group_summary(df: pd.DataFrame, col: str) -> list[dict]:
    if col not in df.columns or df.empty:
        return []
    g = df.groupby(col, dropna=False).agg(
        venda_bruta=("venda_bruta", "sum"),
        venda_liquida=("venda_liquida", "sum"),
        margem_rs=("margem_bruta", "sum"),
        qtd=("quantidade", "sum"),
        n_itens=("_codigo_key", "count"),
    ).reset_index().sort_values("venda_liquida", ascending=False)
    result = []
    for _, r in g.iterrows():
        vl = float(r["venda_liquida"])
        result.append({
            "nome": str(r[col] or "Sem info"),
            "venda_bruta": round(float(r["venda_bruta"]), 2),
            "venda_liquida": round(vl, 2),
            "margem_rs": round(float(r["margem_rs"]), 2),
            "margem_pct": round(float(r["margem_rs"]) / vl * 100, 1) if vl > 0 else 0.0,
            "qtd_kg": round(float(r["qtd"]), 1),
            "n_itens": int(r["n_itens"]),
        })
    return result


def get_analise_categorias(filtros: FiltrosDashboard) -> dict:
    _, df, _ = _get_enriched(filtros)
    return {
        "por_categoria":     _group_summary(df, "categoria"),
        "por_familia":       _group_summary(df, "familia"),
        "por_grupo_produto": _group_summary(df, "grupo_produto"),
    }


def get_analise_supervisores(filtros: FiltrosDashboard) -> dict:
    _, df, _ = _get_enriched(filtros)
    return {
        "por_supervisor": _group_summary(df, "supervisor"),
        "por_vendedor":   _group_summary(df, "vendedor_nome"),
    }


def get_analise_redes(filtros: FiltrosDashboard) -> dict:
    _, df, _ = _get_enriched(filtros)
    if "rede" in df.columns and "n_clientes" not in df.columns:
        # add per-rede client count
        pass
    por_rede: list[dict] = []
    if not df.empty and "rede" in df.columns:
        g = df.groupby("rede", dropna=False).agg(
            venda_bruta=("venda_bruta", "sum"),
            venda_liquida=("venda_liquida", "sum"),
            margem_rs=("margem_bruta", "sum"),
            n_clientes=("cliente_nome", "nunique"),
        ).reset_index().sort_values("venda_liquida", ascending=False)
        for _, r in g.iterrows():
            vl = float(r["venda_liquida"])
            por_rede.append({
                "nome": str(r["rede"] or "Sem rede"),
                "venda_bruta": round(float(r["venda_bruta"]), 2),
                "venda_liquida": round(vl, 2),
                "margem_rs": round(float(r["margem_rs"]), 2),
                "margem_pct": round(float(r["margem_rs"]) / vl * 100, 1) if vl > 0 else 0.0,
                "n_clientes": int(r["n_clientes"]),
            })
    return {"por_rede": por_rede, "por_rota": _group_summary(df, "rota")}


def get_analise_ruptura(filtros: FiltrosDashboard) -> dict:
    _, df, _ = _get_enriched(filtros)
    if df.empty or "ruptura_prevista" not in df.columns:
        return {"total_ruptura_kg": 0, "qtd_itens_ruptura": 0, "por_categoria": [], "por_produto": []}

    df_rupt = df[df["ruptura_prevista"] < 0].copy()
    df_rupt["rupt_abs"] = abs(df_rupt["ruptura_prevista"])

    por_cat = (
        df_rupt.groupby("categoria")["rupt_abs"].sum()
        .nlargest(15).reset_index()
        .to_dict(orient="records")
    )
    por_prod = (
        df_rupt.groupby("descricao")["rupt_abs"].sum()
        .nlargest(15).reset_index()
        .to_dict(orient="records")
    )
    return {
        "total_ruptura_kg": round(float(df_rupt["rupt_abs"].sum()), 2),
        "qtd_itens_ruptura": len(df_rupt),
        "qtd_produtos_ruptura": int(df_rupt["_codigo_key"].nunique()),
        "por_categoria": [{"categoria": r["categoria"], "ruptura_kg": round(r["rupt_abs"], 2)} for r in por_cat],
        "por_produto":   [{"produto": r["descricao"], "ruptura_kg": round(r["rupt_abs"], 2)} for r in por_prod],
    }


def get_analise_logistica(filtros: FiltrosDashboard) -> dict:
    db, df, _ = _get_enriched(filtros)
    if df.empty or "rota" not in df.columns:
        return {"rotas": []}

    refs = _load_refs(db, [])
    df_fr = refs.get("fretes", pd.DataFrame())
    fr_idx = {}
    if not df_fr.empty and "rota" in df_fr.columns:
        df_fr = df_fr.copy()
        for c in ["valor_atual", "pedido_minimo", "tara"]:
            if c in df_fr.columns:
                df_fr[c] = pd.to_numeric(df_fr[c], errors="coerce").fillna(0)
        df_fr["_k"] = df_fr["rota"].fillna("").str.strip()
        for _, row in df_fr.drop_duplicates("_k").iterrows():
            fr_idx[row["_k"]] = {
                "valor_atual": float(row.get("valor_atual") or 0),
                "pedido_minimo": float(row.get("pedido_minimo") or 0),
                "tara": float(row.get("tara") or 0),
            }

    g = df.groupby("rota", dropna=False).agg(
        valor_total=("venda_liquida", "sum"),
        qtd_total=("quantidade", "sum"),
        n_clientes=("cliente_nome", "nunique"),
    ).reset_index().sort_values("valor_total", ascending=False)

    result = []
    for _, r in g.iterrows():
        rota = str(r["rota"] or "Sem rota")
        val = float(r["valor_total"])
        params = fr_idx.get(rota.strip(), {})
        val_min = params.get("valor_atual", 0)
        ped_min = params.get("pedido_minimo", 0)
        thr = max(val_min, ped_min)
        if thr <= 0:
            status = "sem_parametro"
        elif val >= thr:
            status = "viavel"
        elif val < val_min:
            status = "aumentar_valor"
        else:
            status = "aumentar_pedido"
        result.append({
            "rota": rota,
            "valor_total": round(val, 2),
            "qtd_total_kg": round(float(r["qtd_total"]), 1),
            "n_clientes": int(r["n_clientes"]),
            "status_inteligente": status,
            "valor_minimo": val_min,
            "pedido_minimo": ped_min,
            "tara": params.get("tara", 0),
            "ocupacao_valor_pct": round(val / val_min * 100, 1) if val_min > 0 else None,
        })
    return {"rotas": result}


def get_analise_margem(filtros: FiltrosDashboard) -> dict:
    _, df, _ = _get_enriched(filtros)
    if df.empty:
        return {"piores_margens_produto": [], "por_categoria": []}

    df_v = df[df["venda_liquida"] > 0].copy()

    g_prod = df_v.groupby("descricao").agg(
        venda=("venda_liquida", "sum"), margem_rs=("margem_bruta", "sum")
    ).reset_index()
    g_prod["margem_pct"] = (g_prod["margem_rs"] / g_prod["venda"] * 100).round(2)

    g_cat = df_v.groupby("categoria", dropna=False).agg(
        venda=("venda_liquida", "sum"), margem_rs=("margem_bruta", "sum")
    ).reset_index()
    g_cat["margem_pct"] = (g_cat["margem_rs"] / g_cat["venda"] * 100).round(2)
    g_cat = g_cat.sort_values("venda", ascending=False)

    piores = g_prod.nsmallest(15, "margem_pct")
    return {
        "piores_margens_produto": [
            {"produto": r["descricao"], "venda": round(r["venda"], 2),
             "margem_rs": round(r["margem_rs"], 2), "margem_pct": r["margem_pct"]}
            for _, r in piores.iterrows()
        ],
        "por_categoria": [
            {"nome": str(r["categoria"] or "Sem categoria"), "venda": round(r["venda"], 2),
             "margem_rs": round(r["margem_rs"], 2), "margem_pct": r["margem_pct"]}
            for _, r in g_cat.iterrows()
        ],
    }


def get_analise_precos(filtros: FiltrosDashboard) -> dict:
    _, df, _ = _get_enriched(filtros)
    if df.empty or "preco_tabela" not in df.columns:
        return {"divergencias": [], "acima_tabela": 0, "abaixo_tabela": 0, "igual_tabela": 0}

    df_c = df[df["preco_tabela"] > 0].copy()
    if df_c.empty:
        return {"divergencias": [], "acima_tabela": 0, "abaixo_tabela": 0, "igual_tabela": 0}

    df_c["div_pct"] = ((df_c["preco_cx"] - df_c["preco_tabela"]) / df_c["preco_tabela"] * 100).round(2)
    acima = int((df_c["preco_cx"] > df_c["preco_tabela"] * 1.001).sum())
    abaixo = int((df_c["preco_cx"] < df_c["preco_tabela"] * 0.999).sum())
    igual = len(df_c) - acima - abaixo

    g = df_c.groupby("descricao").agg(
        preco_praticado=("preco_cx", "mean"),
        preco_tabela_m=("preco_tabela", "first"),
        div_media=("div_pct", "mean"),
        qtd=("quantidade", "count"),
    ).reset_index().sort_values("div_media", key=abs, ascending=False).head(20)

    divs = []
    for _, r in g.iterrows():
        divs.append({
            "produto": str(r["descricao"]),
            "preco_praticado": round(float(r["preco_praticado"]), 4),
            "preco_tabela": round(float(r["preco_tabela_m"]), 4),
            "divergencia_pct": round(float(r["div_media"]), 2),
            "qtd_vendas": int(r["qtd"]),
        })
    return {"divergencias": divs, "acima_tabela": acima, "abaixo_tabela": abaixo, "igual_tabela": igual}


def get_opcoes_filtros() -> dict:
    """Retorna opções de filtro a partir das tabelas de referência."""
    db = get_service_client()
    vendedores: list[dict] = []
    supervisores: list[str] = []
    redes: list[str] = []
    rotas: list[str] = []
    categorias: list[str] = []
    familias: list[str] = []

    try:
        r = db.table("dim_vendedores").select("codigo,nome,nome_reduzido").limit(500).execute()
        for row in (r.data or []):
            cod = str(row.get("codigo") or "").strip()
            nome = str(row.get("nome_reduzido") or row.get("nome") or cod).strip()
            if cod:
                vendedores.append({"value": cod, "label": f"{cod} — {nome}"})
    except Exception:
        pass

    try:
        r = db.table("dim_supervisor_vendedor").select("supervisor").limit(500).execute()
        supervisores = sorted({str(row["supervisor"]) for row in (r.data or []) if row.get("supervisor")})
    except Exception:
        pass

    try:
        r = db.table("dim_tabela_cliente_rota").select("rede,rota").limit(5000).execute()
        redes = sorted({str(row["rede"]) for row in (r.data or []) if row.get("rede")})
        rotas = sorted({str(row["rota"]) for row in (r.data or []) if row.get("rota")})
    except Exception:
        pass

    try:
        r = db.table("base_categorias").select("categoria,familia").limit(20000).execute()
        categorias = sorted({str(row["categoria"]) for row in (r.data or []) if row.get("categoria")})[:100]
        familias = sorted({str(row["familia"]) for row in (r.data or []) if row.get("familia")})
    except Exception:
        pass

    return {
        "vendedores": vendedores,
        "gestores": [{"value": s, "label": s} for s in supervisores],
        "supervisores": supervisores,
        "categorias": categorias,
        "familias": familias,
        "redes": redes,
        "rotas": rotas,
        "estados": [],
    }
