import { useQuery } from '@tanstack/react-query'
import { RefreshCw, AlertCircle } from 'lucide-react'
import { dashboardApi } from '../services/api'
import { useFilterStore } from '../store'
import { KpiCard, KpiGroup } from '../components/kpi/KpiCard'
import { SimpleBarChart, SimpleLineChart } from '../components/charts/Charts'
import { DataTable } from '../components/tables/DataTable'
import { FilterPanel } from '../components/filters/FilterPanel'
import { Button } from '../components/ui/Button'
import { Card, CardHeader } from '../components/ui/Card'
import { StatusBadge } from '../components/ui/Badge'
import { formatBRL, formatPercent, formatNumber, formatDate } from '../utils/formatters'
import type { KpiDashboard, GraficoDashboard, ResumoTabela, OpcoesFiltros } from '../types'

function buildParams(filtros: Record<string, string | undefined>) {
  return Object.fromEntries(Object.entries(filtros).filter(([, v]) => v))
}

export default function Dashboard() {
  const { filtros, setFiltros } = useFilterStore()
  const params = buildParams(filtros as Record<string, string | undefined>)

  const kpisQ = useQuery<KpiDashboard>({
    queryKey: ['kpis', params],
    queryFn: () => dashboardApi.getKpis(params),
  })

  const graficosQ = useQuery<GraficoDashboard>({
    queryKey: ['graficos', params],
    queryFn: () => dashboardApi.getGraficos(params),
  })

  const resumoVendQ = useQuery<ResumoTabela[]>({
    queryKey: ['resumo-vendedor', params],
    queryFn: () => dashboardApi.getResumoVendedor(params),
  })

  const opcoesQ = useQuery<OpcoesFiltros>({
    queryKey: ['opcoes-filtros'],
    queryFn: dashboardApi.getOpcoesFiltros,
    staleTime: 5 * 60 * 1000,
  })

  const kpis = kpisQ.data
  const graficos = graficosQ.data
  const resumo = resumoVendQ.data || []
  const opcoes = opcoesQ.data || { vendedores: [], gestores: [], categorias: [], redes: [], rotas: [], estados: [] }

  const isLoading = kpisQ.isLoading || graficosQ.isLoading

  return (
    <div className="flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-center justify-between gap-2">
        <div>
          <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Dashboard</h1>
          {kpis?.data_ultimo_upload && (
            <p className="text-xs text-gray-400 mt-0.5">
              Último upload: {formatDate(kpis.data_ultimo_upload)}
            </p>
          )}
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => { kpisQ.refetch(); graficosQ.refetch() }}
          loading={isLoading}
        >
          <RefreshCw className="h-3 w-3" />
          Atualizar
        </Button>
      </div>

      {/* Filtros */}
      <FilterPanel
        opcoes={opcoes}
        onApply={() => { kpisQ.refetch(); graficosQ.refetch(); resumoVendQ.refetch() }}
      />

      {/* Erro */}
      {kpisQ.isError && (
        <div className="flex items-center gap-2 p-2.5 rounded bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-xs text-red-700 dark:text-red-400">
          <AlertCircle className="h-3.5 w-3.5 shrink-0" />
          Erro ao carregar dados. Verifique a conexão com o backend.
        </div>
      )}

      {/* KPI — Vendas */}
      <KpiGroup title="Vendas" columns={4}>
        <KpiCard
          title="Faturamento Bruto"
          value={formatBRL(kpis?.vendas.faturamento_bruto)}
          status="neutral"
        />
        <KpiCard
          title="Faturamento Líquido"
          value={formatBRL(kpis?.vendas.faturamento_liquido)}
          status="positive"
        />
        <KpiCard
          title="Qtd. Vendida"
          value={formatNumber(kpis?.vendas.qtd_vendida, 0)}
          subtitle="caixas"
        />
        <KpiCard
          title="Ticket Médio"
          value={formatBRL(kpis?.vendas.ticket_medio)}
          status="neutral"
        />
      </KpiGroup>

      {/* KPI — Margem */}
      <KpiGroup title="Margem" columns={4}>
        <KpiCard
          title="Margem Bruta"
          value={formatBRL(kpis?.margem.margem_bruta_rs)}
          status="positive"
        />
        <KpiCard
          title="Margem %"
          value={formatPercent(kpis?.margem.margem_bruta_percentual)}
          status={
            (kpis?.margem.margem_bruta_percentual ?? 0) >= 15 ? 'positive' :
            (kpis?.margem.margem_bruta_percentual ?? 0) >= 8 ? 'warning' : 'negative'
          }
        />
        <KpiCard
          title="Desconto Total"
          value={formatBRL(kpis?.margem.desconto_total)}
          status="warning"
        />
        <KpiCard
          title="% Desconto"
          value={formatPercent(kpis?.margem.desconto_percentual)}
          status={
            (kpis?.margem.desconto_percentual ?? 0) <= 5 ? 'positive' :
            (kpis?.margem.desconto_percentual ?? 0) <= 10 ? 'warning' : 'negative'
          }
        />
      </KpiGroup>

      {/* KPI — Meta */}
      <KpiGroup title="Meta" columns={4}>
        <KpiCard
          title="Meta Mensal"
          value={formatBRL(kpis?.meta.meta_mensal)}
        />
        <KpiCard
          title="Meta 115%"
          value={formatBRL(kpis?.meta.meta_115)}
        />
        <KpiCard
          title="Atingimento do Dia"
          value={formatPercent(kpis?.meta.atingimento_percentual)}
          status={kpis?.meta.status_meta === 'acima' ? 'positive' : kpis?.meta.status_meta === 'abaixo' ? 'negative' : 'neutral'}
        />
        <KpiCard
          title="Saldo para Meta"
          value={formatBRL(kpis?.meta.saldo_meta)}
          status={(kpis?.meta.saldo_meta ?? 0) <= 0 ? 'positive' : 'warning'}
        />
      </KpiGroup>

      {/* KPI — Realizado (da planilha de metas) */}
      <KpiGroup title="Realizado" columns={4}>
        <KpiCard
          title="Venda Total Realizada"
          value={formatBRL(kpis?.meta.venda_realizada)}
          status="neutral"
        />
        <KpiCard
          title="Tendência R$"
          value={formatPercent(kpis?.meta.tendencia_rs_pct)}
          subtitle="projeção fim do mês"
          status={
            (kpis?.meta.tendencia_rs_pct ?? 0) >= 100 ? 'positive' :
            (kpis?.meta.tendencia_rs_pct ?? 0) >= 85  ? 'warning'  : 'negative'
          }
        />
        <KpiCard
          title="Tonelagem Realizada"
          value={`${formatNumber(kpis?.meta.tonelagem_realizada, 3)} t`}
          status="neutral"
        />
        <KpiCard
          title="Tendência Kg"
          value={formatPercent(kpis?.meta.tendencia_kg_pct)}
          subtitle="projeção fim do mês"
          status={
            (kpis?.meta.tendencia_kg_pct ?? 0) >= 100 ? 'positive' :
            (kpis?.meta.tendencia_kg_pct ?? 0) >= 85  ? 'warning'  : 'negative'
          }
        />
      </KpiGroup>

      {/* KPI — Ruptura */}
      <KpiGroup title="Ruptura" columns={4}>
        <KpiCard
          title="Ruptura Total"
          value={`${formatNumber(kpis?.ruptura.total_ruptura_kg)} kg`}
          status={(kpis?.ruptura.total_ruptura_kg ?? 0) > 0 ? 'negative' : 'positive'}
        />
        <KpiCard
          title="Produtos c/ Ruptura"
          value={formatNumber(kpis?.ruptura.qtd_produtos_ruptura, 0)}
          status={(kpis?.ruptura.qtd_produtos_ruptura ?? 0) > 0 ? 'negative' : 'positive'}
        />
        <KpiCard
          title="Categorias c/ Ruptura"
          value={formatNumber(kpis?.ruptura.qtd_categorias_ruptura, 0)}
          status={(kpis?.ruptura.qtd_categorias_ruptura ?? 0) > 0 ? 'warning' : 'positive'}
        />
        <KpiCard
          title="Prods. s/ Venda c/ Estoque"
          value={formatNumber(kpis?.ruptura.produtos_sem_venda_com_estoque, 0)}
          status={(kpis?.ruptura.produtos_sem_venda_com_estoque ?? 0) > 0 ? 'warning' : 'neutral'}
        />
      </KpiGroup>

      {/* KPI — Logística */}
      <KpiGroup title="Logística" columns={4}>
        <KpiCard title="Pedidos Viáveis" value={formatNumber(kpis?.logistica.pedidos_viaveis, 0)} status="positive" />
        <KpiCard title="Aumentar Valor" value={formatNumber(kpis?.logistica.pedidos_aumentar_valor, 0)} status={(kpis?.logistica.pedidos_aumentar_valor ?? 0) > 0 ? 'warning' : 'neutral'} />
        <KpiCard title="Aumentar Peso" value={formatNumber(kpis?.logistica.pedidos_aumentar_peso, 0)} status={(kpis?.logistica.pedidos_aumentar_peso ?? 0) > 0 ? 'warning' : 'neutral'} />
        <KpiCard title="Ocupação Média (Peso)" value={formatPercent(kpis?.logistica.ocupacao_media_peso)} />
      </KpiGroup>

      {/* Gráficos — linha 1 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <SimpleBarChart
          data={graficos?.top10_categorias || []}
          title="Top 10 Categorias por Venda Líquida"
          layout="vertical"
        />
        <SimpleBarChart
          data={graficos?.por_vendedor || []}
          title="Vendas por Vendedor"
          layout="vertical"
        />
      </div>

      {/* Gráficos — linha 2 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <SimpleLineChart
          data={graficos?.evolucao_diaria || []}
          title="Evolução Diária — Faturamento e Margem"
        />
        <SimpleBarChart
          data={graficos?.por_rede || []}
          title="Vendas por Rede"
          layout="vertical"
        />
      </div>

      {/* Gráficos — linha 3 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <SimpleBarChart
          data={graficos?.por_gestor || []}
          title="Vendas por Supervisor"
          layout="vertical"
        />
        <SimpleBarChart
          data={graficos?.por_rota || []}
          title="Top 10 Rotas por Venda Líquida"
          layout="vertical"
        />
      </div>

      {/* Gráficos — rupturas e preços */}
      {((graficos?.maiores_rupturas_categoria?.length ?? 0) > 0 ||
        (graficos?.divergencias_preco?.length ?? 0) > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {(graficos?.maiores_rupturas_categoria?.length ?? 0) > 0 && (
            <SimpleBarChart
              data={graficos!.maiores_rupturas_categoria}
              title="Maiores Rupturas por Categoria (kg)"
              layout="vertical"
              formatValue={(v) => `${v.toFixed(0)} kg`}
            />
          )}
          {(graficos?.divergencias_preco?.length ?? 0) > 0 && (
            <SimpleBarChart
              data={graficos!.divergencias_preco}
              title="Maiores Divergências de Preço"
              layout="vertical"
              formatValue={(v) => `R$ ${v.toFixed(2)}`}
            />
          )}
        </div>
      )}

      {/* Tabelas resumo */}
      <Card>
        <CardHeader
          title="Resumo por Vendedor"
          subtitle={`${resumo.length} vendedor(es)`}
        />
        <DataTable
          data={resumo as unknown as Record<string, unknown>[]}
          filename="resumo-vendedor"
          columns={[
            { key: 'nome', label: 'Vendedor', sortable: true },
            {
              key: 'venda_bruta', label: 'V. Bruta', align: 'right', sortable: true,
              render: (v) => formatBRL(Number(v)),
            },
            {
              key: 'venda_liquida', label: 'V. Líquida', align: 'right', sortable: true,
              render: (v) => formatBRL(Number(v)),
            },
            {
              key: 'margem_rs', label: 'Margem R$', align: 'right', sortable: true,
              render: (v) => formatBRL(Number(v)),
            },
            {
              key: 'margem_percentual', label: 'Margem %', align: 'right', sortable: true,
              render: (v) => {
                const p = Number(v)
                const color = p >= 15 ? 'text-green-600 dark:text-green-400' :
                               p >= 8 ? 'text-yellow-600' : 'text-red-600'
                return <span className={color}>{formatPercent(p)}</span>
              },
            },
            { key: 'qtd_pedidos', label: 'Pedidos', align: 'right', sortable: true },
          ]}
        />
      </Card>
    </div>
  )
}
