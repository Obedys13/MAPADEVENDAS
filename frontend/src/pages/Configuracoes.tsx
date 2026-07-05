import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Save, Plus, Trash2, Settings, Target, Truck, Database, History } from 'lucide-react'
import { configApi } from '../services/api'
import { Card, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { DataTable } from '../components/tables/DataTable'
import { StatusBadge } from '../components/ui/Badge'
import { formatDatetime } from '../utils/formatters'

const TABS = [
  { id: 'parametros', label: 'Parâmetros', Icon: Settings },
  { id: 'metas', label: 'Metas', Icon: Target },
  { id: 'logistica', label: 'Logística', Icon: Truck },
  { id: 'bases', label: 'Bases Vigentes', Icon: Database },
  { id: 'historico', label: 'Histórico', Icon: History },
]

export default function Configuracoes() {
  const [tab, setTab] = useState('parametros')
  const qc = useQueryClient()

  // Parâmetros
  const paramsQ = useQuery({ queryKey: ['parametros'], queryFn: configApi.getParametros })
  const [editParam, setEditParam] = useState<Record<string, string>>({})

  const saveParamMut = useMutation({
    mutationFn: ({ chave, valor }: { chave: string; valor: string }) =>
      configApi.setParametro(chave, valor),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['parametros'] }),
  })

  // Metas
  const [anoMeta, setAnoMeta] = useState(new Date().getFullYear())
  const [mesMeta, setMesMeta] = useState(new Date().getMonth() + 1)
  const metasQ = useQuery({
    queryKey: ['metas', anoMeta, mesMeta],
    queryFn: () => configApi.getMetas(anoMeta, mesMeta),
  })
  const [novaMeta, setNovaMeta] = useState({ vendedor: '', gestor: '', meta_valor: '', dias_uteis: '22' })
  const criarMetaMut = useMutation({
    mutationFn: () => configApi.criarMeta({
      ano: anoMeta, mes: mesMeta,
      vendedor: novaMeta.vendedor, gestor: novaMeta.gestor,
      meta_valor: Number(novaMeta.meta_valor),
      dias_uteis: Number(novaMeta.dias_uteis),
    }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['metas'] }); setNovaMeta({ vendedor: '', gestor: '', meta_valor: '', dias_uteis: '22' }) },
  })
  const delMetaMut = useMutation({
    mutationFn: (id: string) => configApi.deletarMeta(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['metas'] }),
  })

  // Logística
  const logisticaQ = useQuery({ queryKey: ['logistica'], queryFn: configApi.getLogistica })
  const [novaRota, setNovaRota] = useState({ rota: '', nome_rota: '', valor_minimo: '', tara_minima: '', pedido_minimo: '', tipo_carro: '', frete_valor: '' })
  const salvarRotaMut = useMutation({
    mutationFn: () => configApi.salvarLogistica({
      rota: novaRota.rota, nome_rota: novaRota.nome_rota,
      valor_minimo: Number(novaRota.valor_minimo),
      tara_minima: Number(novaRota.tara_minima),
      pedido_minimo: Number(novaRota.pedido_minimo),
      tipo_carro: novaRota.tipo_carro,
      frete_valor: Number(novaRota.frete_valor),
    }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['logistica'] }); setNovaRota({ rota: '', nome_rota: '', valor_minimo: '', tara_minima: '', pedido_minimo: '', tipo_carro: '', frete_valor: '' }) },
  })

  // Bases
  const basesQ = useQuery({ queryKey: ['bases-vigentes'], queryFn: configApi.getBasesVigentes })

  // Histórico
  const historicoQ = useQuery({ queryKey: ['historico-cfg'], queryFn: configApi.getHistoricoUploads })

  return (
    <div className="flex flex-col gap-3">
      <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Configurações</h1>

      {/* Tabs */}
      <div className="flex gap-0.5 border-b border-gray-200 dark:border-gray-800">
        {TABS.map(({ id, label, Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-colors ${
              tab === id
                ? 'border-brand-800 dark:border-accent-500 text-brand-800 dark:text-accent-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
            }`}
          >
            <Icon className="h-3.5 w-3.5" />
            {label}
          </button>
        ))}
      </div>

      {/* Parâmetros */}
      {tab === 'parametros' && (
        <Card>
          <CardHeader title="Parâmetros do Sistema" />
          <div className="flex flex-col gap-2">
            {(paramsQ.data || []).map((p: any) => (
              <div key={p.chave} className="flex items-center gap-2">
                <div className="flex-1">
                  <p className="text-xs font-medium text-gray-700 dark:text-gray-300">{p.chave}</p>
                  {p.descricao && <p className="text-2xs text-gray-400">{p.descricao}</p>}
                </div>
                <input
                  value={editParam[p.chave] ?? p.valor}
                  onChange={(e) => setEditParam((prev) => ({ ...prev, [p.chave]: e.target.value }))}
                  className="h-7 w-32 px-2 text-xs border border-gray-200 dark:border-gray-700 rounded bg-white dark:bg-gray-800 focus:outline-none"
                />
                <Button
                  variant="outline"
                  size="xs"
                  onClick={() => saveParamMut.mutate({ chave: p.chave, valor: editParam[p.chave] ?? p.valor })}
                  loading={saveParamMut.isPending}
                >
                  <Save className="h-3 w-3" />
                </Button>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Metas */}
      {tab === 'metas' && (
        <div className="flex flex-col gap-3">
          <Card>
            <CardHeader title="Metas Mensais por Vendedor" actions={
              <div className="flex gap-1">
                <select
                  value={anoMeta}
                  onChange={(e) => setAnoMeta(Number(e.target.value))}
                  className="h-6 text-xs border border-gray-200 dark:border-gray-700 rounded px-1.5 bg-white dark:bg-gray-800"
                >
                  {[2024, 2025, 2026, 2027].map((y) => <option key={y}>{y}</option>)}
                </select>
                <select
                  value={mesMeta}
                  onChange={(e) => setMesMeta(Number(e.target.value))}
                  className="h-6 text-xs border border-gray-200 dark:border-gray-700 rounded px-1.5 bg-white dark:bg-gray-800"
                >
                  {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                    <option key={m} value={m}>{m.toString().padStart(2, '0')}</option>
                  ))}
                </select>
              </div>
            } />
            <DataTable
              data={metasQ.data || []}
              filename="metas"
              columns={[
                { key: 'vendedor', label: 'Vendedor' },
                { key: 'gestor', label: 'Gestor' },
                { key: 'meta_valor', label: 'Meta', align: 'right', render: (v) => `R$ ${Number(v).toLocaleString('pt-BR')}` },
                { key: 'meta_115_percent', label: 'Meta 115%', align: 'right', render: (v) => `R$ ${Number(v).toLocaleString('pt-BR')}` },
                { key: 'dias_uteis', label: 'Dias Úteis', align: 'center' },
                { key: 'meta_diaria', label: 'Meta/Dia', align: 'right', render: (v) => `R$ ${Number(v).toLocaleString('pt-BR')}` },
                {
                  key: 'id', label: '', sortable: false,
                  render: (v) => (
                    <Button variant="ghost" size="xs" onClick={() => delMetaMut.mutate(String(v))}>
                      <Trash2 className="h-3 w-3 text-red-500" />
                    </Button>
                  ),
                },
              ]}
            />
          </Card>
          <Card>
            <CardHeader title="Nova Meta" />
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <Input label="Vendedor" value={novaMeta.vendedor} onChange={(e) => setNovaMeta((p) => ({ ...p, vendedor: e.target.value }))} />
              <Input label="Gestor" value={novaMeta.gestor} onChange={(e) => setNovaMeta((p) => ({ ...p, gestor: e.target.value }))} />
              <Input label="Meta (R$)" type="number" value={novaMeta.meta_valor} onChange={(e) => setNovaMeta((p) => ({ ...p, meta_valor: e.target.value }))} />
              <Input label="Dias Úteis" type="number" value={novaMeta.dias_uteis} onChange={(e) => setNovaMeta((p) => ({ ...p, dias_uteis: e.target.value }))} />
            </div>
            <Button variant="primary" size="sm" className="mt-2" onClick={() => criarMetaMut.mutate()} loading={criarMetaMut.isPending}>
              <Plus className="h-3 w-3" /> Adicionar Meta
            </Button>
          </Card>
        </div>
      )}

      {/* Logística */}
      {tab === 'logistica' && (
        <div className="flex flex-col gap-3">
          <Card>
            <CardHeader title="Parâmetros de Logística por Rota" />
            <DataTable
              data={logisticaQ.data || []}
              filename="logistica"
              columns={[
                { key: 'rota', label: 'Rota', sortable: true },
                { key: 'nome_rota', label: 'Nome' },
                { key: 'valor_minimo', label: 'Val. Mín. (R$)', align: 'right' },
                { key: 'tara_minima', label: 'Tara Mín. (kg)', align: 'right' },
                { key: 'pedido_minimo', label: 'Pedido Mín.', align: 'right' },
                { key: 'tipo_carro', label: 'Tipo Carro' },
                { key: 'frete_valor', label: 'Frete', align: 'right' },
              ]}
            />
          </Card>
          <Card>
            <CardHeader title="Nova Rota" />
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <Input label="Código Rota" value={novaRota.rota} onChange={(e) => setNovaRota((p) => ({ ...p, rota: e.target.value }))} />
              <Input label="Nome Rota" value={novaRota.nome_rota} onChange={(e) => setNovaRota((p) => ({ ...p, nome_rota: e.target.value }))} />
              <Input label="Valor Mínimo" type="number" value={novaRota.valor_minimo} onChange={(e) => setNovaRota((p) => ({ ...p, valor_minimo: e.target.value }))} />
              <Input label="Tara Mínima (kg)" type="number" value={novaRota.tara_minima} onChange={(e) => setNovaRota((p) => ({ ...p, tara_minima: e.target.value }))} />
              <Input label="Pedido Mínimo" type="number" value={novaRota.pedido_minimo} onChange={(e) => setNovaRota((p) => ({ ...p, pedido_minimo: e.target.value }))} />
              <Input label="Tipo de Carro" value={novaRota.tipo_carro} onChange={(e) => setNovaRota((p) => ({ ...p, tipo_carro: e.target.value }))} />
              <Input label="Frete (R$)" type="number" value={novaRota.frete_valor} onChange={(e) => setNovaRota((p) => ({ ...p, frete_valor: e.target.value }))} />
            </div>
            <Button variant="primary" size="sm" className="mt-2" onClick={() => salvarRotaMut.mutate()} loading={salvarRotaMut.isPending}>
              <Plus className="h-3 w-3" /> Salvar Rota
            </Button>
          </Card>
        </div>
      )}

      {/* Bases vigentes */}
      {tab === 'bases' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <Card>
            <CardHeader title="Versões de Produtos" />
            <table className="w-full text-xs">
              <thead><tr className="border-b border-gray-100 dark:border-gray-800">
                {['Tipo', 'Upload', 'Início Vigência', 'Fim Vigência', 'Ativo'].map((h) => (
                  <th key={h} className="px-2 py-1.5 text-left font-medium text-gray-500">{h}</th>
                ))}
              </tr></thead>
              <tbody>
                {(basesQ.data?.produtos || []).map((v: any) => (
                  <tr key={v.id} className="border-b border-gray-50 dark:border-gray-800/50">
                    <td className="px-2 py-1.5">{v.tipo_base}</td>
                    <td className="px-2 py-1.5">{v.data_upload}</td>
                    <td className="px-2 py-1.5">{v.periodo_inicio_vigencia}</td>
                    <td className="px-2 py-1.5">{v.periodo_fim_vigencia || '—'}</td>
                    <td className="px-2 py-1.5">
                      <StatusBadge status={v.ativo ? 'concluido' : 'pendente'} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
          <Card>
            <CardHeader title="Versões de Clientes" />
            <table className="w-full text-xs">
              <thead><tr className="border-b border-gray-100 dark:border-gray-800">
                {['Tipo', 'Upload', 'Início Vigência', 'Fim Vigência', 'Ativo'].map((h) => (
                  <th key={h} className="px-2 py-1.5 text-left font-medium text-gray-500">{h}</th>
                ))}
              </tr></thead>
              <tbody>
                {(basesQ.data?.clientes || []).map((v: any) => (
                  <tr key={v.id} className="border-b border-gray-50 dark:border-gray-800/50">
                    <td className="px-2 py-1.5">{v.tipo_base}</td>
                    <td className="px-2 py-1.5">{v.data_upload}</td>
                    <td className="px-2 py-1.5">{v.periodo_inicio_vigencia}</td>
                    <td className="px-2 py-1.5">{v.periodo_fim_vigencia || '—'}</td>
                    <td className="px-2 py-1.5">
                      <StatusBadge status={v.ativo ? 'concluido' : 'pendente'} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </div>
      )}

      {/* Histórico */}
      {tab === 'historico' && (
        <Card>
          <CardHeader title="Histórico de Uploads" />
          <DataTable
            data={historicoQ.data || []}
            filename="historico-uploads"
            columns={[
              { key: 'tipo', label: 'Tipo', sortable: true },
              { key: 'data_referencia', label: 'Data Ref.' },
              { key: 'arquivo_original', label: 'Arquivo' },
              { key: 'usuario', label: 'Usuário' },
              { key: 'data_hora_upload', label: 'Data Upload', render: (v) => formatDatetime(String(v)) },
              { key: 'total_registros', label: 'Registros', align: 'right' },
              { key: 'status', label: 'Status', render: (v) => <StatusBadge status={String(v)} /> },
            ]}
          />
        </Card>
      )}
    </div>
  )
}
