import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { FileDown, FileText, FileSpreadsheet, Printer } from 'lucide-react'
import { relatoriosApi } from '../services/api'
import { Card, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { formatBRL, formatPercent } from '../utils/formatters'

const RELATORIOS = [
  { id: 'vendas', nome: 'Relatório Diário de Vendas', descricao: 'Faturamento, margem, ruptura e resumo por vendedor do dia.' },
  { id: 'ruptura', nome: 'Relatório de Ruptura', descricao: 'Produtos e categorias com ruptura prevista.' },
  { id: 'logistica', nome: 'Relatório Logístico', descricao: 'Status de rotas, ocupação e pedidos mínimos.' },
  { id: 'dde', nome: 'Relatório DDE', descricao: 'Demanda, estoque e ressuprimento por categoria.' },
  { id: 'margem', nome: 'Relatório de Margem', descricao: 'Análise de margem por produto, vendedor e categoria.' },
]

export default function Relatorios() {
  const [dataInicio, setDataInicio] = useState(new Date().toISOString().split('T')[0])
  const [dataFim, setDataFim] = useState(new Date().toISOString().split('T')[0])
  const [vendedor, setVendedor] = useState('')
  const [tipoSel, setTipoSel] = useState('vendas')

  const diarioQ = useQuery({
    queryKey: ['relatorio-diario', dataInicio],
    queryFn: () => relatoriosApi.diario(dataInicio),
    enabled: false,
  })

  const params = {
    data_inicio: dataInicio || undefined,
    data_fim: dataFim || undefined,
    vendedor: vendedor || undefined,
    tipo: tipoSel,
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Relatórios</h1>
        <p className="text-xs text-gray-400 mt-0.5">Geração e exportação de relatórios analíticos</p>
      </div>

      {/* Seleção de parâmetros */}
      <Card>
        <CardHeader title="Parâmetros do Relatório" />
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <Input label="Data Início" type="date" value={dataInicio} onChange={(e) => setDataInicio(e.target.value)} />
          <Input label="Data Fim" type="date" value={dataFim} onChange={(e) => setDataFim(e.target.value)} />
          <Input label="Vendedor (opcional)" value={vendedor} onChange={(e) => setVendedor(e.target.value)} placeholder="Todos" />
        </div>
      </Card>

      {/* Lista de relatórios */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {RELATORIOS.map((rel) => (
          <div key={rel.id} className="card p-3 flex flex-col gap-2">
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">{rel.nome}</h3>
              <p className="text-2xs text-gray-400 mt-0.5">{rel.descricao}</p>
            </div>
            <div className="flex items-center gap-1.5 mt-auto">
              <Button
                variant="outline"
                size="xs"
                onClick={() => relatoriosApi.exportCsv({ ...params, tipo: rel.id })}
                title="Exportar CSV"
              >
                <FileText className="h-3 w-3" />
                CSV
              </Button>
              <Button
                variant="outline"
                size="xs"
                onClick={() => relatoriosApi.exportExcel({ ...params, tipo: rel.id })}
                title="Exportar Excel"
              >
                <FileSpreadsheet className="h-3 w-3" />
                Excel
              </Button>
            </div>
          </div>
        ))}
      </div>

      {/* Relatório diário rápido */}
      <Card>
        <CardHeader
          title="Relatório Diário Rápido"
          subtitle={`Data: ${dataInicio}`}
          actions={
            <Button variant="primary" size="sm" onClick={() => diarioQ.refetch()} loading={diarioQ.isFetching}>
              Gerar
            </Button>
          }
        />
        {diarioQ.data && (
          <div className="flex flex-col gap-3 animate-fade-in">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {[
                { label: 'Faturamento Líquido', value: formatBRL(diarioQ.data.faturamento_liquido) },
                { label: 'Margem Bruta', value: formatBRL(diarioQ.data.margem_bruta_rs) },
                { label: 'Margem %', value: formatPercent(diarioQ.data.margem_bruta_pct) },
                { label: 'Ruptura (kg)', value: `${diarioQ.data.ruptura_kg} kg` },
              ].map((kpi) => (
                <div key={kpi.label} className="flex flex-col gap-0.5 p-2 rounded border border-gray-100 dark:border-gray-800">
                  <span className="text-2xs text-gray-400">{kpi.label}</span>
                  <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">{kpi.value}</span>
                </div>
              ))}
            </div>

            {diarioQ.data.por_vendedor?.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-gray-100 dark:border-gray-800">
                      <th className="px-2 py-1.5 text-left font-medium text-gray-500">Vendedor</th>
                      <th className="px-2 py-1.5 text-right font-medium text-gray-500">Venda</th>
                      <th className="px-2 py-1.5 text-right font-medium text-gray-500">Margem</th>
                    </tr>
                  </thead>
                  <tbody>
                    {diarioQ.data.por_vendedor.map((v: any) => (
                      <tr key={v.vendedor} className="border-b border-gray-50 dark:border-gray-800/50">
                        <td className="px-2 py-1.5">{v.vendedor}</td>
                        <td className="px-2 py-1.5 text-right tabular-nums">{formatBRL(v.venda)}</td>
                        <td className="px-2 py-1.5 text-right tabular-nums">{formatBRL(v.margem)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="flex gap-2">
              <Button variant="ghost" size="xs" onClick={() => window.print()}>
                <Printer className="h-3 w-3" /> Imprimir
              </Button>
              <Button
                variant="ghost"
                size="xs"
                onClick={() => relatoriosApi.exportCsv({ data_inicio: dataInicio, data_fim: dataInicio, tipo: 'vendas' })}
              >
                <FileDown className="h-3 w-3" /> Exportar CSV
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  )
}
