import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Lightbulb, AlertTriangle, TrendingDown, Truck, Tag, Users, Network, DollarSign } from 'lucide-react'
import { analisesApi } from '../services/api'
import { useFilterStore } from '../store'
import { Card, CardHeader } from '../components/ui/Card'
import { DataTable } from '../components/tables/DataTable'
import { SimpleBarChart } from '../components/charts/Charts'
import { Input } from '../components/ui/Input'
import { formatBRL, formatNumber } from '../utils/formatters'

function buildParams(filtros: Record<string, string | undefined>) {
  return Object.fromEntries(Object.entries(filtros).filter(([, v]) => v)) as Record<string, string>
}

export default function Analises() {
  const { filtros } = useFilterStore()
  const [dataRef, setDataRef] = useState(new Date().toISOString().split('T')[0])

  const params = buildParams({
    ...filtros,
    data_inicio: filtros.data_inicio || dataRef,
    data_fim: filtros.data_fim || dataRef,
  } as Record<string, string | undefined>)

  const insightsQ    = useQuery({ queryKey: ['insights', params],    queryFn: () => analisesApi.insights(params) })
  const categoriasQ  = useQuery({ queryKey: ['categorias', params],  queryFn: () => analisesApi.categorias(params) })
  const supervisoresQ= useQuery({ queryKey: ['supervisores', params], queryFn: () => analisesApi.supervisores(params) })
  const redesQ       = useQuery({ queryKey: ['redes', params],       queryFn: () => analisesApi.redes(params) })
  const rupturaQ     = useQuery({ queryKey: ['ruptura', params],     queryFn: () => analisesApi.ruptura(params) })
  const margemQ      = useQuery({ queryKey: ['margem-analise', params], queryFn: () => analisesApi.margem(params) })
  const logisticaQ   = useQuery({ queryKey: ['logistica', params],   queryFn: () => analisesApi.logistica(params) })
  const precosQ      = useQuery({ queryKey: ['precos', params],      queryFn: () => analisesApi.precos(params) })
  const ddeQ         = useQuery({ queryKey: ['dde', dataRef],        queryFn: () => analisesApi.dde(dataRef) })

  const insights: string[] = insightsQ.data?.insights || []
  const categorias = categoriasQ.data
  const supervisores = supervisoresQ.data
  const redes = redesQ.data
  const ruptura = rupturaQ.data
  const margem = margemQ.data
  const logistica = logisticaQ.data?.rotas || []
  const precos = precosQ.data
  const ddeData = ddeQ.data?.data || []

  const colsVenda = [
    { key: 'nome',           label: 'Nome',       sortable: true },
    { key: 'venda_bruta',    label: 'V. Bruta',   align: 'right' as const, sortable: true,
      render: (v: unknown) => formatBRL(Number(v)) },
    { key: 'venda_liquida',  label: 'V. Líquida', align: 'right' as const, sortable: true,
      render: (v: unknown) => formatBRL(Number(v)) },
    { key: 'margem_rs',      label: 'Margem R$',  align: 'right' as const, sortable: true,
      render: (v: unknown) => formatBRL(Number(v)) },
    { key: 'margem_pct',     label: 'Margem %',   align: 'right' as const, sortable: true,
      render: (v: unknown) => {
        const p = Number(v)
        return <span className={p < 0 ? 'text-red-600' : p < 10 ? 'text-yellow-600' : 'text-green-600 dark:text-green-400'}>{p.toFixed(1)}%</span>
      } },
    { key: 'qtd_kg',         label: 'Qtd (kg)',   align: 'right' as const, render: (v: unknown) => formatNumber(Number(v), 0) },
    { key: 'n_itens',        label: 'Itens',      align: 'right' as const },
  ]

  return (
    <div className="flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between gap-2">
        <div>
          <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Análises</h1>
          <p className="text-xs text-gray-400 mt-0.5">Análises detalhadas com dados enriquecidos</p>
        </div>
        <Input type="date" value={dataRef} onChange={(e) => setDataRef(e.target.value)} className="w-auto" />
      </div>

      {/* Insights */}
      <Card>
        <CardHeader title="Insights Automáticos" subtitle="Gerados com base nos dados do período"
          actions={<Lightbulb className="h-4 w-4 text-yellow-500" />} />
        {insights.length === 0
          ? <p className="text-xs text-gray-400">Nenhum insight disponível.</p>
          : <ul className="flex flex-col gap-1.5">
              {insights.map((t, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-gray-700 dark:text-gray-300">
                  <span className="w-1.5 h-1.5 rounded-full bg-brand-800 dark:bg-brand-400 mt-1.5 shrink-0" />
                  {t}
                </li>
              ))}
            </ul>
        }
      </Card>

      {/* Categorias */}
      {categorias && (
        <>
          <Card>
            <CardHeader title="Vendas por Categoria" actions={<Tag className="h-4 w-4 text-gray-400" />} />
            <DataTable data={categorias.por_categoria || []} filename="por-categoria" columns={colsVenda} />
          </Card>
          {(categorias.por_familia || []).length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <SimpleBarChart
                data={(categorias.por_familia || []).slice(0, 10).map((r: any) => ({ label: r.nome, valor: r.venda_liquida }))}
                title="Vendas por Família"
                layout="vertical"
              />
              {(categorias.por_grupo_produto || []).length > 0 && (
                <SimpleBarChart
                  data={(categorias.por_grupo_produto || []).slice(0, 10).map((r: any) => ({ label: r.nome, valor: r.venda_liquida }))}
                  title="Vendas por Grupo de Produto"
                  layout="vertical"
                />
              )}
            </div>
          )}
        </>
      )}

      {/* Supervisores */}
      {supervisores && (supervisores.por_supervisor || []).length > 0 && (
        <>
          <Card>
            <CardHeader title="Vendas por Supervisor" actions={<Users className="h-4 w-4 text-gray-400" />} />
            <DataTable data={supervisores.por_supervisor || []} filename="por-supervisor" columns={colsVenda} />
          </Card>
          <Card>
            <CardHeader title="Vendas por Vendedor" />
            <DataTable data={supervisores.por_vendedor || []} filename="por-vendedor" columns={colsVenda} />
          </Card>
        </>
      )}

      {/* Redes e Rotas */}
      {redes && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {(redes.por_rede || []).length > 0 && (
            <Card>
              <CardHeader title="Vendas por Rede" actions={<Network className="h-4 w-4 text-gray-400" />} />
              <DataTable
                data={redes.por_rede || []}
                filename="por-rede"
                columns={[
                  { key: 'nome',          label: 'Rede',       sortable: true },
                  { key: 'venda_liquida', label: 'V. Líquida', align: 'right' as const, render: (v: unknown) => formatBRL(Number(v)) },
                  { key: 'margem_pct',    label: 'Margem %',   align: 'right' as const, render: (v: unknown) => `${Number(v).toFixed(1)}%` },
                  { key: 'n_clientes',    label: 'Clientes',   align: 'right' as const },
                ]}
              />
            </Card>
          )}
          {(redes.por_rota || []).length > 0 && (
            <Card>
              <CardHeader title="Vendas por Rota" />
              <DataTable
                data={redes.por_rota || []}
                filename="por-rota"
                columns={[
                  { key: 'nome',          label: 'Rota',       sortable: true },
                  { key: 'venda_liquida', label: 'V. Líquida', align: 'right' as const, render: (v: unknown) => formatBRL(Number(v)) },
                  { key: 'margem_pct',    label: 'Margem %',   align: 'right' as const, render: (v: unknown) => `${Number(v).toFixed(1)}%` },
                  { key: 'n_itens',       label: 'Itens',      align: 'right' as const },
                ]}
              />
            </Card>
          )}
        </div>
      )}

      {/* Ruptura */}
      {ruptura && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <SimpleBarChart
            data={(ruptura.por_categoria || []).map((r: any) => ({ label: r.categoria, valor: r.ruptura_kg }))}
            title={`Top Rupturas por Categoria — ${ruptura.total_ruptura_kg?.toFixed(1) ?? 0} kg total`}
            layout="vertical"
            formatValue={(v) => `${v.toFixed(0)} kg`}
          />
          <SimpleBarChart
            data={(ruptura.por_produto || []).map((r: any) => ({ label: r.produto, valor: r.ruptura_kg }))}
            title="Top Rupturas por Produto (kg)"
            layout="vertical"
            formatValue={(v) => `${v.toFixed(0)} kg`}
          />
        </div>
      )}

      {/* Margem */}
      {margem && (
        <>
          {(margem.piores_margens_produto || []).length > 0 && (
            <Card>
              <CardHeader title="Produtos com Menor Margem" actions={<TrendingDown className="h-4 w-4 text-red-500" />} />
              <DataTable
                data={margem.piores_margens_produto}
                filename="piores-margens"
                columns={[
                  { key: 'produto',    label: 'Produto',   sortable: true },
                  { key: 'venda',      label: 'Venda',     align: 'right' as const, render: (v: unknown) => formatBRL(Number(v)) },
                  { key: 'margem_rs',  label: 'Margem R$', align: 'right' as const, render: (v: unknown) => formatBRL(Number(v)) },
                  { key: 'margem_pct', label: 'Margem %',  align: 'right' as const, sortable: true,
                    render: (v: unknown) => {
                      const p = Number(v)
                      return <span className={p < 0 ? 'text-red-600' : p < 10 ? 'text-yellow-600' : ''}>{p.toFixed(1)}%</span>
                    } },
                ]}
              />
            </Card>
          )}
        </>
      )}

      {/* Logística */}
      {logistica.length > 0 && (
        <Card>
          <CardHeader title="Status Logístico por Rota" actions={<Truck className="h-4 w-4 text-gray-400" />} />
          <DataTable
            data={logistica}
            filename="logistica-rotas"
            columns={[
              { key: 'rota',              label: 'Rota',         sortable: true },
              { key: 'valor_total',       label: 'Valor',        align: 'right' as const, render: (v: unknown) => formatBRL(Number(v)) },
              { key: 'qtd_total_kg',      label: 'Qtd (kg)',     align: 'right' as const, render: (v: unknown) => `${formatNumber(Number(v), 0)} kg` },
              { key: 'n_clientes',        label: 'Clientes',     align: 'right' as const },
              { key: 'valor_minimo',      label: 'Mín. Valor',   align: 'right' as const, render: (v: unknown) => v ? formatBRL(Number(v)) : '—' },
              { key: 'status_inteligente', label: 'Status',
                render: (v: unknown) => {
                  const s = String(v || '')
                  const cls = s === 'viavel' ? 'text-green-600 dark:text-green-400'
                            : s.includes('aumentar') || s.includes('pedido') ? 'text-yellow-600'
                            : 'text-gray-400'
                  const label = s === 'viavel' ? 'Viável' : s === 'aumentar_valor' ? 'Aumentar Valor' : s === 'aumentar_pedido' ? 'Aumentar Pedido' : s || '—'
                  return <span className={cls}>{label}</span>
                } },
              { key: 'ocupacao_valor_pct', label: 'Ocupação %', align: 'right' as const,
                render: (v: unknown) => v != null ? `${Number(v).toFixed(0)}%` : '—' },
            ]}
          />
        </Card>
      )}

      {/* Preços */}
      {precos && (precos.divergencias || []).length > 0 && (
        <Card>
          <CardHeader
            title="Divergências de Preço vs. Tabela"
            subtitle={`${precos.acima_tabela ?? 0} acima • ${precos.abaixo_tabela ?? 0} abaixo • ${precos.igual_tabela ?? 0} igual`}
            actions={<DollarSign className="h-4 w-4 text-gray-400" />}
          />
          <DataTable
            data={precos.divergencias}
            filename="divergencias-preco"
            columns={[
              { key: 'produto',          label: 'Produto',          sortable: true },
              { key: 'preco_praticado',  label: 'Preço Praticado',  align: 'right' as const, render: (v: unknown) => formatBRL(Number(v)) },
              { key: 'preco_tabela',     label: 'Preço Tabela',     align: 'right' as const, render: (v: unknown) => formatBRL(Number(v)) },
              { key: 'divergencia_pct',  label: 'Divergência %',    align: 'right' as const, sortable: true,
                render: (v: unknown) => {
                  const p = Number(v)
                  return <span className={p > 0 ? 'text-red-600' : p < 0 ? 'text-green-600' : ''}>{p > 0 ? '+' : ''}{p.toFixed(1)}%</span>
                } },
              { key: 'qtd_vendas',       label: 'Qtd Vendas',       align: 'right' as const },
            ]}
          />
        </Card>
      )}

      {/* DDE */}
      {ddeData.length > 0 && (
        <Card>
          <CardHeader title="DDE — Demanda, Estoque e Ressuprimento" />
          <DataTable
            data={ddeData}
            filename="dde"
            columns={[
              { key: 'categoria',     label: 'Categoria',   sortable: true },
              { key: 'meta_kg',       label: 'Meta (kg)',   align: 'right' as const, render: (v: unknown) => formatNumber(Number(v), 0) },
              { key: 'venda_kg',      label: 'Venda (kg)',  align: 'right' as const, render: (v: unknown) => formatNumber(Number(v), 0) },
              { key: 'estoque_kg',    label: 'Estoque (kg)',align: 'right' as const, render: (v: unknown) => formatNumber(Number(v), 0) },
              { key: 'ruptura_kg',    label: 'Ruptura (kg)',align: 'right' as const, render: (v: unknown) => {
                const n = Number(v); return <span className={n > 0 ? 'text-red-600' : ''}>{formatNumber(n, 0)}</span>
              }},
              { key: 'excesso_rs',    label: 'Excesso R$',  align: 'right' as const, render: (v: unknown) => formatBRL(Number(v)) },
              { key: 'dias_estoque',  label: 'Dias Est.',   align: 'right' as const, render: (v: unknown) => formatNumber(Number(v), 1) },
              { key: 'perc_resultado',label: '% Result.',   align: 'right' as const, render: (v: unknown) => `${(Number(v)*100).toFixed(0)}%` },
            ]}
          />
        </Card>
      )}
    </div>
  )
}
