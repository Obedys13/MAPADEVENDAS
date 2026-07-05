from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from datetime import date
from typing import Optional
from ...core.auth import get_current_user
from ...core.database import get_service_client
from ...services.upload_service import processar_upload, confirmar_importacao
from ...schemas.uploads import UploadPreview, HistoricoUpload

router = APIRouter(prefix="/uploads", tags=["uploads"])

TIPOS_VALIDOS = {
    # DIÁRIAS — substituem automaticamente o upload do mesmo dia
    "mapa_vendas", "lista_precos", "estoque", "dde", "meta_vendedor",
    # FIXAS — substituem todos os dados ao re-importar
    "planilha_produtos", "planilha_clientes",
    "base_categorias", "tipos_tabela_preco", "vendedores", "tabela_cliente_rota",
    "tabela_fretes", "tabela_grupo_rede", "tabela_supervisor_vendedor",
}


@router.post("/{tipo}/preview", response_model=UploadPreview)
async def upload_preview(
    tipo: str,
    arquivo: UploadFile = File(...),
    data_referencia: Optional[date] = Form(None),
    _user: dict = Depends(get_current_user),
):
    if tipo not in TIPOS_VALIDOS:
        raise HTTPException(400, f"Tipo inválido: {tipo}. Válidos: {', '.join(TIPOS_VALIDOS)}")
    if not arquivo.filename.endswith(".xlsx"):
        raise HTTPException(400, "Apenas arquivos .xlsx são aceitos.")

    content = await arquivo.read()
    return await processar_upload(
        content=content,
        tipo=tipo,
        data_referencia=data_referencia,
        arquivo_nome=arquivo.filename,
        usuario=_user.get("sub", "admin"),
    )


@router.post("/{tipo}/confirmar")
async def upload_confirmar(
    tipo: str,
    upload_id: str = Form(...),
    arquivo: UploadFile = File(...),
    data_referencia: Optional[date] = Form(None),
    substituir: bool = Form(False),
    _user: dict = Depends(get_current_user),
):
    if tipo not in TIPOS_VALIDOS:
        raise HTTPException(400, f"Tipo inválido: {tipo}")

    content = await arquivo.read()
    result = await confirmar_importacao(
        upload_id=upload_id,
        content=content,
        tipo=tipo,
        data_referencia=data_referencia,
        substituir=substituir,
    )
    if not result.get("ok"):
        raise HTTPException(422, result.get("mensagem", "Erro no processamento."))
    return result


@router.get("/historico", response_model=list[HistoricoUpload])
def historico_uploads(
    tipo: Optional[str] = None,
    limit: int = 50,
    _user: dict = Depends(get_current_user),
):
    db = get_service_client()
    query = db.table("uploads").select("*").order("data_hora_upload", desc=True).limit(limit)
    if tipo:
        query = query.eq("tipo", tipo)
    result = query.execute()
    return result.data or []


@router.get("/{upload_id}/status")
def upload_status(upload_id: str, _user: dict = Depends(get_current_user)):
    db = get_service_client()
    result = db.table("uploads").select("*").eq("id", upload_id).execute()
    if not result.data:
        raise HTTPException(404, "Upload não encontrado.")
    return result.data[0]


@router.get("/{upload_id}/logs")
def upload_logs(upload_id: str, _user: dict = Depends(get_current_user)):
    db = get_service_client()
    result = db.table("upload_logs").select("*").eq("upload_id", upload_id).order(
        "created_at"
    ).execute()
    return result.data or []
