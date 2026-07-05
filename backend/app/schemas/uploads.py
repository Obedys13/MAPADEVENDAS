from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, Any
from uuid import UUID


class UploadResponse(BaseModel):
    id: UUID
    tipo: str
    data_referencia: Optional[date]
    status: str
    total_registros: Optional[int]
    registros_processados: Optional[int]
    mensagem_erro: Optional[str]
    data_hora_upload: datetime


class UploadPreview(BaseModel):
    upload_id: UUID
    tipo: str
    total_registros: int
    colunas_encontradas: list[str]
    colunas_ausentes: list[str]
    avisos: list[str]
    erros: list[str]
    preview_linhas: list[dict[str, Any]]
    pode_importar: bool


class HistoricoUpload(BaseModel):
    id: UUID
    tipo: str
    data_referencia: Optional[date]
    usuario: str
    data_hora_upload: datetime
    status: str
    total_registros: Optional[int]
    arquivo_original: Optional[str]
