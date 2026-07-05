from pydantic import BaseModel
from datetime import date
from typing import Optional


class KpiVendas(BaseModel):
    faturamento_bruto: float = 0
    faturamento_liquido: float = 0
    qtd_vendida: float = 0
    ticket_medio: float = 0
    preco_medio: float = 0
    qtd_pedidos: int = 0
    qtd_clientes: int = 0
    qtd_produtos: int = 0


class KpiMargem(BaseModel):
    margem_bruta_rs: float = 0
    margem_bruta_percentual: float = 0
    desconto_total: float = 0
    desconto_percentual: float = 0


class KpiMeta(BaseModel):
    meta_mensal: float = 0
    meta_115: float = 0
    meta_diaria: float = 0
    realizado_dia: float = 0
    realizado_acumulado: float = 0
    atingimento_percentual: float = 0
    saldo_meta: float = 0
    status_meta: str = "sem_dados"
    atingimento_115_percentual: float = 0
    # Realizados
    venda_realizada: float = 0
    tendencia_rs_pct: float = 0
    tonelagem_realizada: float = 0
    tendencia_kg_pct: float = 0


class KpiRuptura(BaseModel):
    total_ruptura_kg: float = 0
    qtd_produtos_ruptura: int = 0
    qtd_categorias_ruptura: int = 0
    produtos_sem_venda_com_estoque: int = 0
    categorias_sem_venda_com_estoque: int = 0


class KpiLogistica(BaseModel):
    pedidos_viaveis: int = 0
    pedidos_aumentar_valor: int = 0
    pedidos_aumentar_peso: int = 0
    ocupacao_media_peso: float = 0
    ocupacao_media_valor: float = 0
    total_rotas: int = 0


class KpiDashboard(BaseModel):
    data_referencia: Optional[date]
    data_ultimo_upload: Optional[date]
    vendas: KpiVendas
    margem: KpiMargem
    meta: KpiMeta
    ruptura: KpiRuptura
    logistica: KpiLogistica


class GraficoItem(BaseModel):
    label: str
    valor: float
    secundario: Optional[float] = None


class GraficoDashboard(BaseModel):
    top10_categorias: list[GraficoItem] = []
    top10_produtos: list[GraficoItem] = []
    por_vendedor: list[GraficoItem] = []
    por_gestor: list[GraficoItem] = []
    por_rede: list[GraficoItem] = []
    por_rota: list[GraficoItem] = []
    evolucao_diaria: list[GraficoItem] = []
    meta_vs_realizado: list[GraficoItem] = []
    # Negativos
    categorias_sem_venda_com_estoque: list[GraficoItem] = []
    produtos_sem_venda_com_estoque: list[GraficoItem] = []
    maiores_rupturas_categoria: list[GraficoItem] = []
    maiores_rupturas_produto: list[GraficoItem] = []
    divergencias_preco: list[GraficoItem] = []


class ResumoTabela(BaseModel):
    nome: str
    venda_bruta: float = 0
    venda_liquida: float = 0
    margem_rs: float = 0
    margem_percentual: float = 0
    quantidade: float = 0
    qtd_pedidos: int = 0
    status_meta: Optional[str] = None


class FiltrosDashboard(BaseModel):
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    mes: Optional[int] = None
    ano: Optional[int] = None
    vendedor: Optional[str] = None
    gestor: Optional[str] = None
    categoria: Optional[str] = None
    produto: Optional[str] = None
    familia: Optional[str] = None
    grupo_produto: Optional[str] = None
    cliente: Optional[str] = None
    rede: Optional[str] = None
    rota: Optional[str] = None
    estado: Optional[str] = None
    tipo_saida: Optional[str] = None
    status_ruptura: Optional[str] = None
    status_desconto: Optional[str] = None
    status_logistico: Optional[str] = None
