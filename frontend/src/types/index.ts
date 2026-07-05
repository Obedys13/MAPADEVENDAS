export interface KpiVendas {
  faturamento_bruto: number
  faturamento_liquido: number
  qtd_vendida: number
  ticket_medio: number
  preco_medio: number
  qtd_pedidos: number
  qtd_clientes: number
  qtd_produtos: number
}

export interface KpiMargem {
  margem_bruta_rs: number
  margem_bruta_percentual: number
  desconto_total: number
  desconto_percentual: number
}

export interface KpiMeta {
  meta_mensal: number
  meta_115: number
  meta_diaria: number
  realizado_dia: number
  realizado_acumulado: number
  atingimento_percentual: number
  saldo_meta: number
  status_meta: 'acima' | 'abaixo' | 'no_prazo' | 'sem_dados'
  atingimento_115_percentual: number
  venda_realizada: number
  tendencia_rs_pct: number
  tonelagem_realizada: number
  tendencia_kg_pct: number
}

export interface KpiRuptura {
  total_ruptura_kg: number
  qtd_produtos_ruptura: number
  qtd_categorias_ruptura: number
  produtos_sem_venda_com_estoque: number
  categorias_sem_venda_com_estoque: number
}

export interface KpiLogistica {
  pedidos_viaveis: number
  pedidos_aumentar_valor: number
  pedidos_aumentar_peso: number
  ocupacao_media_peso: number
  ocupacao_media_valor: number
  total_rotas: number
}

export interface KpiDashboard {
  data_referencia: string | null
  data_ultimo_upload: string | null
  vendas: KpiVendas
  margem: KpiMargem
  meta: KpiMeta
  ruptura: KpiRuptura
  logistica: KpiLogistica
}

export interface GraficoItem {
  label: string
  valor: number
  secundario?: number
}

export interface GraficoDashboard {
  top10_categorias: GraficoItem[]
  top10_produtos: GraficoItem[]
  por_vendedor: GraficoItem[]
  por_gestor: GraficoItem[]
  por_rede: GraficoItem[]
  por_rota: GraficoItem[]
  evolucao_diaria: GraficoItem[]
  maiores_rupturas_categoria: GraficoItem[]
  divergencias_preco: GraficoItem[]
}

export interface ResumoTabela {
  nome: string
  venda_bruta: number
  venda_liquida: number
  margem_rs: number
  margem_percentual: number
  quantidade: number
  qtd_pedidos: number
  status_meta?: string
}

export interface UploadHistorico {
  id: string
  tipo: string
  data_referencia: string | null
  usuario: string
  data_hora_upload: string
  status: 'pendente' | 'processando' | 'concluido' | 'erro' | 'aguardando_confirmacao'
  total_registros: number | null
  arquivo_original: string | null
}

export interface UploadPreview {
  upload_id: string
  tipo: string
  total_registros: number
  colunas_encontradas: string[]
  colunas_ausentes: string[]
  avisos: string[]
  erros: string[]
  preview_linhas: Record<string, unknown>[]
  pode_importar: boolean
}

export interface FiltrosDashboard {
  data_inicio?: string
  data_fim?: string
  vendedor?: string
  gestor?: string
  categoria?: string
  produto?: string
  familia?: string
  grupo_produto?: string
  cliente?: string
  rede?: string
  rota?: string
  estado?: string
  tipo_saida?: string
  status_ruptura?: string
  status_desconto?: string
  status_logistico?: string
}

export interface MetaMensal {
  id: string
  ano: number
  mes: number
  vendedor: string
  gestor: string | null
  meta_valor: number
  meta_115_percent: number
  dias_uteis: number
  meta_diaria: number
}

export interface OpcoesFiltros {
  vendedores: Array<{ value: string; label: string } | string>
  gestores: Array<{ value: string; label: string } | string>
  supervisores?: string[]
  categorias: string[]
  familias?: string[]
  redes: string[]
  rotas: string[]
  estados: string[]
}
