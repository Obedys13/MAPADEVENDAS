import { useState, useMemo } from 'react'
import { ChevronUp, ChevronDown, ChevronsUpDown, Download, Search } from 'lucide-react'
import { cn } from '../../utils/cn'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { exportToCsv } from '../../utils/formatters'

export interface Column<T> {
  key: keyof T | string
  label: string
  render?: (value: unknown, row: T) => React.ReactNode
  sortable?: boolean
  align?: 'left' | 'right' | 'center'
  className?: string
  headerClassName?: string
}

interface DataTableProps<T extends Record<string, unknown>> {
  data: T[]
  columns: Column<T>[]
  filename?: string
  searchable?: boolean
  exportable?: boolean
  pageSize?: number
  className?: string
  emptyMessage?: string
}

export function DataTable<T extends Record<string, unknown>>({
  data,
  columns,
  filename = 'export',
  searchable = true,
  exportable = true,
  pageSize = 20,
  className,
  emptyMessage = 'Nenhum dado encontrado.',
}: DataTableProps<T>) {
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState<string | null>(null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [page, setPage] = useState(1)

  const filtered = useMemo(() => {
    if (!search.trim()) return data
    const s = search.toLowerCase()
    return data.filter((row) =>
      Object.values(row).some((v) => String(v ?? '').toLowerCase().includes(s))
    )
  }, [data, search])

  const sorted = useMemo(() => {
    if (!sortKey) return filtered
    return [...filtered].sort((a, b) => {
      const av = a[sortKey]
      const bv = b[sortKey]
      const cmp =
        typeof av === 'number' && typeof bv === 'number'
          ? av - bv
          : String(av ?? '').localeCompare(String(bv ?? ''))
      return sortDir === 'asc' ? cmp : -cmp
    })
  }, [filtered, sortKey, sortDir])

  const totalPages = Math.ceil(sorted.length / pageSize)
  const paged = sorted.slice((page - 1) * pageSize, page * pageSize)

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
    setPage(1)
  }

  return (
    <div className={cn('flex flex-col gap-2', className)}>
      {(searchable || exportable) && (
        <div className="flex items-center justify-between gap-2">
          {searchable && (
            <div className="relative w-48">
              <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-gray-400 pointer-events-none" />
              <input
                type="text"
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(1) }}
                placeholder="Buscar..."
                className="h-7 w-full pl-6 pr-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-xs focus:outline-none focus:ring-1 focus:ring-brand-800 dark:focus:ring-accent-500"
              />
            </div>
          )}
          <div className="flex items-center gap-1 ml-auto">
            <span className="text-2xs text-gray-400">{sorted.length} registros</span>
            {exportable && (
              <Button
                variant="ghost"
                size="xs"
                onClick={() => exportToCsv(sorted as Record<string, unknown>[], `${filename}.csv`)}
                title="Exportar CSV"
              >
                <Download className="h-3 w-3" />
              </Button>
            )}
          </div>
        </div>
      )}

      <div className="overflow-x-auto -mx-0">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              {columns.map((col) => (
                <th
                  key={String(col.key)}
                  className={cn(
                    'px-2 py-1.5 text-left font-semibold text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800/50 whitespace-nowrap',
                    col.align === 'right' && 'text-right',
                    col.align === 'center' && 'text-center',
                    col.sortable !== false && 'cursor-pointer select-none hover:text-gray-700 dark:hover:text-gray-200',
                    col.headerClassName
                  )}
                  onClick={() => col.sortable !== false && handleSort(String(col.key))}
                >
                  <span className="inline-flex items-center gap-0.5">
                    {col.label}
                    {col.sortable !== false && (
                      sortKey === String(col.key) ? (
                        sortDir === 'asc' ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />
                      ) : (
                        <ChevronsUpDown className="h-3 w-3 opacity-30" />
                      )
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paged.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-2 py-6 text-center text-gray-400 text-xs">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              paged.map((row, i) => (
                <tr
                  key={i}
                  className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/40 transition-colors"
                >
                  {columns.map((col) => {
                    const val = row[String(col.key)]
                    return (
                      <td
                        key={String(col.key)}
                        className={cn(
                          'px-2 py-1.5 text-gray-700 dark:text-gray-300',
                          col.align === 'right' && 'text-right tabular-nums',
                          col.align === 'center' && 'text-center',
                          col.className
                        )}
                      >
                        {col.render ? col.render(val, row) : String(val ?? '—')}
                      </td>
                    )
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between gap-2 pt-1">
          <span className="text-2xs text-gray-400">
            Página {page} de {totalPages}
          </span>
          <div className="flex gap-1">
            <Button variant="outline" size="xs" disabled={page === 1} onClick={() => setPage(1)}>«</Button>
            <Button variant="outline" size="xs" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>‹</Button>
            <Button variant="outline" size="xs" disabled={page === totalPages} onClick={() => setPage((p) => p + 1)}>›</Button>
            <Button variant="outline" size="xs" disabled={page === totalPages} onClick={() => setPage(totalPages)}>»</Button>
          </div>
        </div>
      )}
    </div>
  )
}
