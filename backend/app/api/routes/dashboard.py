from fastapi import APIRouter, Depends, Query
from datetime import date
from typing import Optional
from ...core.auth import get_current_user
from ...schemas.dashboard import (
    KpiDashboard, GraficoDashboard, ResumoTabela, FiltrosDashboard
)
from ...services import kpi_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _build_filtros(
    data_inicio: Optional[date] = Query(None),
    data_fim: Optional[date] = Query(None),
    mes: Optional[int] = Query(None),
    ano: Optional[int] = Query(None),
    vendedor: Optional[str] = Query(None),
    gestor: Optional[str] = Query(None),
    categoria: Optional[str] = Query(None),
    produto: Optional[str] = Query(None),
    familia: Optional[str] = Query(None),
    grupo_produto: Optional[str] = Query(None),
    cliente: Optional[str] = Query(None),
    rede: Optional[str] = Query(None),
    rota: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    tipo_saida: Optional[str] = Query(None),
    status_ruptura: Optional[str] = Query(None),
    status_desconto: Optional[str] = Query(None),
    status_logistico: Optional[str] = Query(None),
) -> FiltrosDashboard:
    return FiltrosDashboard(
        data_inicio=data_inicio, data_fim=data_fim,
        mes=mes, ano=ano, vendedor=vendedor, gestor=gestor,
        categoria=categoria, produto=produto, familia=familia,
        grupo_produto=grupo_produto, cliente=cliente, rede=rede,
        rota=rota, estado=estado, tipo_saida=tipo_saida,
        status_ruptura=status_ruptura, status_desconto=status_desconto,
        status_logistico=status_logistico,
    )


@router.get("/kpis", response_model=KpiDashboard)
def get_kpis(
    filtros: FiltrosDashboard = Depends(_build_filtros),
    _user: dict = Depends(get_current_user),
):
    return kpi_service.get_kpis(filtros)


@router.get("/graficos", response_model=GraficoDashboard)
def get_graficos(
    filtros: FiltrosDashboard = Depends(_build_filtros),
    _user: dict = Depends(get_current_user),
):
    return kpi_service.get_graficos(filtros)


@router.get("/resumo/vendedor", response_model=list[ResumoTabela])
def resumo_vendedor(
    filtros: FiltrosDashboard = Depends(_build_filtros),
    _user: dict = Depends(get_current_user),
):
    return kpi_service.get_resumo_vendedor(filtros)


@router.get("/filtros/opcoes")
def opcoes_filtros(_user: dict = Depends(get_current_user)):
    """Retorna opções de filtro a partir das tabelas de referência."""
    return kpi_service.get_opcoes_filtros()
