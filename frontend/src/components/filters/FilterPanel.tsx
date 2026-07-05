import { useState } from 'react'
import { ChevronDown, ChevronUp, Filter, X } from 'lucide-react'
import { Button } from '../ui/Button'
import { Select, Input } from '../ui/Input'
import { useFilterStore } from '../../store'
import type { OpcoesFiltros } from '../../types'
import { cn } from '../../utils/cn'

interface FilterPanelProps {
  opcoes: OpcoesFiltros
  onApply: () => void
}

export function FilterPanel({ opcoes, onApply }: FilterPanelProps) {
  const [open, setOpen] = useState(false)
  const { filtros, setFiltros, clearFiltros } = useFilterStore()

  const hasFilters = Object.values(filtros).some(Boolean)

  const apply = () => {
    onApply()
    setOpen(false)
  }

  const clear = () => {
    clearFiltros()
    onApply()
  }

  return (
    <div className="card p-0 overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center justify-between w-full px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Filter className="h-3.5 w-3.5 text-gray-400" />
          <span className="text-xs font-medium text-gray-700 dark:text-gray-300">Filtros</span>
          {hasFilters && (
            <span className="inline-flex items-center justify-center h-4 w-4 rounded-full bg-brand-800 dark:bg-accent-500 text-white text-2xs font-medium">
              {Object.values(filtros).filter(Boolean).length}
            </span>
          )}
        </div>
        {open ? (
          <ChevronUp className="h-3.5 w-3.5 text-gray-400" />
        ) : (
          <ChevronDown className="h-3.5 w-3.5 text-gray-400" />
        )}
      </button>

      {open && (
        <div className="border-t border-gray-100 dark:border-gray-800 p-3 animate-fade-in">
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
            <Input
              label="Data início"
              type="date"
              value={filtros.data_inicio || ''}
              onChange={(e) => setFiltros({ data_inicio: e.target.value || undefined })}
            />
            <Input
              label="Data fim"
              type="date"
              value={filtros.data_fim || ''}
              onChange={(e) => setFiltros({ data_fim: e.target.value || undefined })}
            />
            <Select
              label="Vendedor"
              value={filtros.vendedor || ''}
              onChange={(e) => setFiltros({ vendedor: e.target.value || undefined })}
              options={opcoes.vendedores.map((v) =>
                typeof v === 'string' ? { value: v, label: v } : v
              )}
              placeholder="Todos"
            />
            <Select
              label="Supervisor"
              value={filtros.gestor || ''}
              onChange={(e) => setFiltros({ gestor: e.target.value || undefined })}
              options={(opcoes.supervisores || opcoes.gestores || []).map((v) =>
                typeof v === 'string' ? { value: v, label: v } : v
              )}
              placeholder="Todos"
            />
            <Select
              label="Categoria"
              value={filtros.categoria || ''}
              onChange={(e) => setFiltros({ categoria: e.target.value || undefined })}
              options={opcoes.categorias.map((v) => ({ value: v, label: v }))}
              placeholder="Todas"
            />
            <Select
              label="Rede"
              value={filtros.rede || ''}
              onChange={(e) => setFiltros({ rede: e.target.value || undefined })}
              options={opcoes.redes.map((v) => ({ value: v, label: v }))}
              placeholder="Todas"
            />
            <Select
              label="Rota"
              value={filtros.rota || ''}
              onChange={(e) => setFiltros({ rota: e.target.value || undefined })}
              options={opcoes.rotas.map((v) => ({ value: v, label: v }))}
              placeholder="Todas"
            />
            <Select
              label="Estado"
              value={filtros.estado || ''}
              onChange={(e) => setFiltros({ estado: e.target.value || undefined })}
              options={opcoes.estados.map((v) => ({ value: v, label: v }))}
              placeholder="Todos"
            />
            <Select
              label="Status Logístico"
              value={filtros.status_logistico || ''}
              onChange={(e) => setFiltros({ status_logistico: e.target.value || undefined })}
              options={[
                { value: 'viavel', label: 'Viável' },
                { value: 'aumentar_valor', label: 'Aumentar Valor' },
                { value: 'aumentar_peso', label: 'Aumentar Peso' },
              ]}
              placeholder="Todos"
            />
            <Select
              label="Status Desconto"
              value={filtros.status_desconto || ''}
              onChange={(e) => setFiltros({ status_desconto: e.target.value || undefined })}
              options={[
                { value: 'sem_desconto', label: 'Sem Desconto' },
                { value: 'com_desconto', label: 'Com Desconto' },
                { value: 'abaixo_tabela', label: 'Abaixo da Tabela' },
                { value: 'acima_tabela', label: 'Acima da Tabela' },
              ]}
              placeholder="Todos"
            />
          </div>

          <div className="flex items-center gap-2 mt-3 pt-3 border-t border-gray-100 dark:border-gray-800">
            <Button variant="primary" size="sm" onClick={apply}>
              Aplicar Filtros
            </Button>
            {hasFilters && (
              <Button variant="ghost" size="sm" onClick={clear}>
                <X className="h-3 w-3" />
                Limpar
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
