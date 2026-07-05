import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Upload, BarChart3, FileText, Settings,
  ChevronLeft, ChevronRight, LogOut,
} from 'lucide-react'
import { cn } from '../../utils/cn'
import { useAuthStore } from '../../store'

interface SidebarProps {
  open: boolean
  mobile?: boolean
  onToggle: () => void
}

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', Icon: LayoutDashboard },
  { to: '/upload', label: 'Upload', Icon: Upload },
  { to: '/analises', label: 'Análises', Icon: BarChart3 },
  { to: '/relatorios', label: 'Relatórios', Icon: FileText },
  { to: '/configuracoes', label: 'Configurações', Icon: Settings },
]

export function Sidebar({ open, mobile, onToggle }: SidebarProps) {
  const logout = useAuthStore((s) => s.logout)

  return (
    <aside
      className={cn(
        'flex flex-col bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 transition-all duration-200 shrink-0',
        mobile
          ? 'fixed left-0 top-0 bottom-0 z-50 w-52 shadow-xl'
          : open ? 'w-48' : 'w-12'
      )}
    >
      {/* Logo */}
      <div className="flex items-center gap-2 px-2.5 py-3 border-b border-gray-100 dark:border-gray-800">
        <div className="w-6 h-6 rounded bg-brand-800 dark:bg-accent-500 flex items-center justify-center shrink-0">
          <span className="text-white text-2xs font-bold">GDM</span>
        </div>
        {(open || mobile) && (
          <div className="flex flex-col min-w-0">
            <span className="text-xs font-semibold text-gray-900 dark:text-gray-100 leading-tight truncate">
              Grupo Doce Mel
            </span>
            <span className="text-2xs text-gray-400 leading-tight">Mapa de Vendas</span>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 py-2 overflow-y-auto">
        {NAV_ITEMS.map(({ to, label, Icon }) => (
          <NavLink
            key={to}
            to={to}
            onClick={mobile ? onToggle : undefined}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-2.5 px-2.5 py-2 mx-1.5 rounded transition-colors text-xs font-medium',
                isActive
                  ? 'bg-brand-800/10 text-brand-800 dark:bg-accent-500/10 dark:text-accent-400'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-100'
              )
            }
            title={!open && !mobile ? label : undefined}
          >
            <Icon className="h-4 w-4 shrink-0" />
            {(open || mobile) && <span className="truncate">{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-gray-100 dark:border-gray-800 p-2">
        <button
          onClick={logout}
          title="Sair"
          className="flex items-center gap-2 px-2 py-1.5 w-full rounded text-xs text-gray-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
        >
          <LogOut className="h-3.5 w-3.5 shrink-0" />
          {(open || mobile) && 'Sair'}
        </button>
        {!mobile && (
          <button
            onClick={onToggle}
            className="flex items-center gap-2 px-2 py-1.5 w-full rounded text-xs text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors mt-0.5"
          >
            {open ? (
              <ChevronLeft className="h-3.5 w-3.5 shrink-0" />
            ) : (
              <ChevronRight className="h-3.5 w-3.5 shrink-0" />
            )}
            {open && 'Recolher'}
          </button>
        )}
      </div>
    </aside>
  )
}
