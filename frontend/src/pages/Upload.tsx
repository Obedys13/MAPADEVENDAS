import { useQuery } from '@tanstack/react-query'
import { uploadsApi } from '../services/api'
import { UploadCard } from '../components/upload/UploadCard'
import type { UploadHistorico } from '../types'

const DIARIAS = [
  { tipo: 'mapa_vendas',  nome: 'Mapa de Vendas',    descricao: 'Pedidos do dia. Substitui automaticamente o upload anterior do mesmo dia.' },
  { tipo: 'lista_precos', nome: 'Lista de Preços',    descricao: 'Tabela de preços vigente por produto. Atualizada diariamente.' },
  { tipo: 'estoque',      nome: 'Estoque Analítico',  descricao: 'Posição de estoque atual por produto. Substitui o do mesmo dia.' },
  { tipo: 'dde',          nome: 'DDE',                descricao: 'Meta, venda e estoque por categoria. Substitui o do mesmo dia.' },
  { tipo: 'meta_vendedor', nome: 'Meta por Vendedor', descricao: 'Meta, venda atual, tendência e positivação por vendedor. Substitui o do mesmo dia.' },
]

const FIXAS = [
  { tipo: 'planilha_clientes',   nome: 'Clientes',             descricao: 'Cadastro completo de clientes. Substitui a versão anterior ao re-importar.' },
  { tipo: 'planilha_produtos',   nome: 'Produtos',             descricao: 'Catálogo de produtos com pesos, conversão e classificações.' },
  { tipo: 'base_categorias',     nome: 'Categorias',           descricao: 'Mapeamento de produto → categoria, família e grupo.' },
  { tipo: 'tipos_tabela_preco',  nome: 'Tipos Tabela de Preço',descricao: 'Cadastro de tabelas de preço com vigência e condições.' },
  { tipo: 'vendedores',          nome: 'Vendedores',           descricao: 'Cadastro de vendedores com supervisor e gerente.' },
  { tipo: 'tabela_cliente_rota',        nome: 'Cliente × Rota',        descricao: 'Vínculo cliente × vendedor × tabela de preço × rota × rede.' },
  { tipo: 'tabela_fretes',              nome: 'Fretes',                descricao: 'Parâmetros de frete por rota: carro, valor mínimo, tara e % despesa.' },
  { tipo: 'tabela_grupo_rede',          nome: 'Grupo × Rede',          descricao: 'Mapeamento de código de grupo para nome da rede/cliente.' },
  { tipo: 'tabela_supervisor_vendedor', nome: 'Supervisor × Vendedor', descricao: 'Vínculo vendedor × supervisor com localidade.' },
]

export default function Upload() {
  const historicoQ = useQuery<UploadHistorico[]>({
    queryKey: ['historico-uploads'],
    queryFn: () => uploadsApi.historico(undefined, 100),
    refetchInterval: 10_000,
  })

  const historico = historicoQ.data || []

  function lastUpload(tipo: string) {
    return historico.find((h) => h.tipo === tipo)
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Upload de Arquivos</h1>
        <p className="text-xs text-gray-400 mt-0.5">
          Planos diários substituem automaticamente o upload do mesmo dia. Planos fixos substituem tudo ao re-importar.
        </p>
      </div>

      {/* Planos Diários */}
      <section>
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
          Planos Diários
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {DIARIAS.map((item) => (
            <UploadCard
              key={item.tipo}
              tipo={item.tipo}
              nome={item.nome}
              descricao={item.descricao}
              lastUpload={lastUpload(item.tipo)}
              isDaily
              onSuccess={() => historicoQ.refetch()}
            />
          ))}
        </div>
      </section>

      {/* Planos Fixos */}
      <section>
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
          Planos Fixos
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {FIXAS.map((item) => (
            <UploadCard
              key={item.tipo}
              tipo={item.tipo}
              nome={item.nome}
              descricao={item.descricao}
              lastUpload={lastUpload(item.tipo)}
              onSuccess={() => historicoQ.refetch()}
            />
          ))}
        </div>
      </section>

      {/* Histórico recente */}
      {historico.length > 0 && (
        <section>
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Histórico Recente
          </h2>
          <div className="card p-0 overflow-hidden">
            <table className="w-full text-xs">
              <thead className="bg-gray-50 dark:bg-gray-800/50">
                <tr>
                  {['Tipo', 'Data Ref.', 'Arquivo', 'Usuário', 'Data Upload', 'Registros', 'Status'].map((h) => (
                    <th key={h} className="px-2 py-1.5 text-left font-medium text-gray-500 dark:text-gray-400 whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {historico.slice(0, 20).map((h) => (
                  <tr key={h.id} className="border-t border-gray-100 dark:border-gray-800">
                    <td className="px-2 py-1.5 font-medium text-gray-700 dark:text-gray-300">{h.tipo}</td>
                    <td className="px-2 py-1.5 text-gray-500">{h.data_referencia || '—'}</td>
                    <td className="px-2 py-1.5 text-gray-500 max-w-32 truncate">{h.arquivo_original || '—'}</td>
                    <td className="px-2 py-1.5 text-gray-500">{h.usuario}</td>
                    <td className="px-2 py-1.5 text-gray-500 whitespace-nowrap">
                      {new Date(h.data_hora_upload).toLocaleString('pt-BR')}
                    </td>
                    <td className="px-2 py-1.5 text-gray-500 text-right">{h.total_registros ?? '—'}</td>
                    <td className="px-2 py-1.5">
                      <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-2xs font-medium ${
                        h.status === 'concluido' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                        h.status === 'erro' ? 'bg-red-100 text-red-800' :
                        h.status === 'processando' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-600'
                      }`}>{h.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  )
}
