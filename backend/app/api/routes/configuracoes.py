from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import date
from typing import Optional
from ...core.auth import get_current_user
from ...core.database import get_service_client

router = APIRouter(prefix="/configuracoes", tags=["configuracoes"])


class MetaMensalInput(BaseModel):
    ano: int
    mes: int
    vendedor: str
    gestor: Optional[str] = None
    meta_valor: float
    dias_uteis: int = 22


class ParametroInput(BaseModel):
    chave: str
    valor: str


class LogisticaInput(BaseModel):
    rota: str
    nome_rota: Optional[str] = None
    valor_minimo: float = 0
    tara_minima: float = 0
    pedido_minimo: float = 0
    tipo_carro: Optional[str] = None
    frete_valor: float = 0


@router.get("/parametros")
def listar_parametros(_user: dict = Depends(get_current_user)):
    db = get_service_client()
    return db.table("parametros_sistema").select("*").execute().data or []


@router.put("/parametros")
def atualizar_parametro(body: ParametroInput, _user: dict = Depends(get_current_user)):
    db = get_service_client()
    db.table("parametros_sistema").upsert(
        {"chave": body.chave, "valor": body.valor, "updated_at": "now()"}
    ).execute()
    return {"ok": True}


@router.get("/metas")
def listar_metas(
    ano: Optional[int] = None,
    mes: Optional[int] = None,
    _user: dict = Depends(get_current_user),
):
    db = get_service_client()
    query = db.table("metas_mensais").select("*")
    if ano:
        query = query.eq("ano", ano)
    if mes:
        query = query.eq("mes", mes)
    return query.order("vendedor").execute().data or []


@router.post("/metas")
def criar_meta(body: MetaMensalInput, _user: dict = Depends(get_current_user)):
    db = get_service_client()
    db.table("metas_mensais").upsert({
        "ano": body.ano, "mes": body.mes, "vendedor": body.vendedor,
        "gestor": body.gestor, "meta_valor": body.meta_valor,
        "dias_uteis": body.dias_uteis,
    }).execute()
    return {"ok": True}


@router.delete("/metas/{meta_id}")
def deletar_meta(meta_id: str, _user: dict = Depends(get_current_user)):
    db = get_service_client()
    db.table("metas_mensais").delete().eq("id", meta_id).execute()
    return {"ok": True}


@router.get("/logistica")
def listar_logistica(_user: dict = Depends(get_current_user)):
    db = get_service_client()
    return db.table("parametros_logistica").select("*").execute().data or []


@router.post("/logistica")
def salvar_logistica(body: LogisticaInput, _user: dict = Depends(get_current_user)):
    db = get_service_client()
    db.table("parametros_logistica").upsert({
        "rota": body.rota, "nome_rota": body.nome_rota,
        "valor_minimo": body.valor_minimo, "tara_minima": body.tara_minima,
        "pedido_minimo": body.pedido_minimo, "tipo_carro": body.tipo_carro,
        "frete_valor": body.frete_valor,
    }).execute()
    return {"ok": True}


@router.get("/bases-vigentes")
def bases_vigentes(_user: dict = Depends(get_current_user)):
    db = get_service_client()
    produtos = db.table("produto_base_versions").select("*").order(
        "data_upload", desc=True
    ).limit(10).execute().data or []
    clientes = db.table("cliente_base_versions").select("*").order(
        "data_upload", desc=True
    ).limit(10).execute().data or []
    return {"produtos": produtos, "clientes": clientes}


@router.get("/historico-uploads")
def historico_uploads(
    limit: int = 100,
    _user: dict = Depends(get_current_user),
):
    db = get_service_client()
    return db.table("uploads").select("*").order(
        "data_hora_upload", desc=True
    ).limit(limit).execute().data or []
