from fastapi import APIRouter, Depends, Query
from datetime import date
from typing import Optional
from ...core.auth import get_current_user
from ...schemas.dashboard import FiltrosDashboard
from ...services import kpi_service
from ...core.database import get_service_client

router = APIRouter(prefix="/analises", tags=["analises"])


def _build_filtros(
    data_inicio: Optional[date] = Query(None),
    data_fim: Optional[date] = Query(None),
    vendedor: Optional[str] = Query(None),
    gestor: Optional[str] = Query(None),
    categoria: Optional[str] = Query(None),
    rede: Optional[str] = Query(None),
    rota: Optional[str] = Query(None),
) -> FiltrosDashboard:
    return FiltrosDashboard(
        data_inicio=data_inicio, data_fim=data_fim,
        vendedor=vendedor, gestor=gestor,
        categoria=categoria, rede=rede, rota=rota,
    )


@router.get("/insights")
def insights(
    filtros: FiltrosDashboard = Depends(_build_filtros),
    _user: dict = Depends(get_current_user),
):
    return {"insights": kpi_service.gerar_insights(filtros)}


@router.get("/categorias")
def analise_categorias(
    filtros: FiltrosDashboard = Depends(_build_filtros),
    _user: dict = Depends(get_current_user),
):
    return kpi_service.get_analise_categorias(filtros)


@router.get("/supervisores")
def analise_supervisores(
    filtros: FiltrosDashboard = Depends(_build_filtros),
    _user: dict = Depends(get_current_user),
):
    return kpi_service.get_analise_supervisores(filtros)


@router.get("/redes")
def analise_redes(
    filtros: FiltrosDashboard = Depends(_build_filtros),
    _user: dict = Depends(get_current_user),
):
    return kpi_service.get_analise_redes(filtros)


@router.get("/ruptura")
def analise_ruptura(
    filtros: FiltrosDashboard = Depends(_build_filtros),
    _user: dict = Depends(get_current_user),
):
    return kpi_service.get_analise_ruptura(filtros)


@router.get("/dde")
def analise_dde(
    data_referencia: Optional[date] = Query(None),
    _user: dict = Depends(get_current_user),
):
    db = get_service_client()
    query = db.table("dde_itens").select("*").order("data_referencia", desc=True)
    if data_referencia:
        query = query.eq("data_referencia", str(data_referencia))
    rows = query.limit(500).execute().data or []
    return {"data": rows}


@router.get("/logistica")
def analise_logistica(
    filtros: FiltrosDashboard = Depends(_build_filtros),
    _user: dict = Depends(get_current_user),
):
    return kpi_service.get_analise_logistica(filtros)


@router.get("/margem")
def analise_margem(
    filtros: FiltrosDashboard = Depends(_build_filtros),
    _user: dict = Depends(get_current_user),
):
    return kpi_service.get_analise_margem(filtros)


@router.get("/precos")
def analise_precos(
    filtros: FiltrosDashboard = Depends(_build_filtros),
    _user: dict = Depends(get_current_user),
):
    return kpi_service.get_analise_precos(filtros)


@router.get("/diagnostico/clientes")
def diagnostico_clientes(_user: dict = Depends(get_current_user)):
    """Diagnostica quais clientes do mapa não encontram correspondência na tabela de rota."""
    db = get_service_client()
    try:
        mapa_rows = db.table("mapa_vendas_itens").select("cliente_nome, venda_bruta") \
            .order("mapa_upload_id", desc=True).limit(5000).execute().data or []
        ref_rows = db.table("dim_tabela_cliente_rota").select("nome, rota, rede, vendedor").limit(2000).execute().data or []

        import pandas as pd
        df_mapa = pd.DataFrame(mapa_rows)
        df_ref = pd.DataFrame(ref_rows) if ref_rows else pd.DataFrame(columns=["nome", "rota", "rede", "vendedor"])

        if df_mapa.empty:
            return {"erro": "Sem dados no mapa"}

        df_mapa["_k"] = df_mapa["cliente_nome"].fillna("").str.strip().str.upper()
        df_mapa["venda_bruta"] = pd.to_numeric(df_mapa["venda_bruta"], errors="coerce").fillna(0)
        ref_keys = set(df_ref["nome"].fillna("").str.strip().str.upper().tolist()) if not df_ref.empty else set()

        resumo = (
            df_mapa.groupby("_k")
            .agg(venda_total=("venda_bruta", "sum"), n_itens=("_k", "count"))
            .reset_index()
            .rename(columns={"_k": "cliente_nome_mapa"})
        )
        resumo["encontrado_na_tabela"] = resumo["cliente_nome_mapa"].isin(ref_keys)
        resumo = resumo.sort_values("venda_total", ascending=False)

        matched = resumo[resumo["encontrado_na_tabela"]].to_dict(orient="records")
        unmatched = resumo[~resumo["encontrado_na_tabela"]].to_dict(orient="records")

        return {
            "total_clientes_mapa": len(resumo),
            "clientes_com_match": len(matched),
            "clientes_sem_match": len(unmatched),
            "venda_com_match": float(resumo[resumo["encontrado_na_tabela"]]["venda_total"].sum()),
            "venda_sem_match": float(resumo[~resumo["encontrado_na_tabela"]]["venda_total"].sum()),
            "amostra_tabela_rota": df_ref["nome"].dropna().head(10).tolist(),
            "sem_match": unmatched,
            "com_match": matched,
        }
    except Exception as e:
        return {"erro": str(e)}
