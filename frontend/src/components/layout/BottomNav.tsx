import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Upload, BarChart3, FileText, Settings } from 'lucide-react'
import { cn } from '../../utils/cn'

const ITEMS = [
  { to: '/dashboard', label: 'Dashboard', Icon: LayoutDashboard },
  { to: '/upload', label: 'Upload', Icon: Upload },
  { to: '/analises', label: 'Análises', Icon: BarChart3 },
  { to: '/relatorios', label: 'Relatórios', Icon: FileText },
  { to: '/configuracoes', label: 'Config', Icon: Settings },
]

export function BottomNav() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-30 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 flex safe-area-padding">
      {ITEMS.map(({ to, label, Icon }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) =>
            cn(
              'flex flex-col items-center justify-center flex-1 py-2 gap-0.5 text-2xs font-medium transition-colors',
              isActive
                ? 'text-brand-800 dark:text-accent-400'
                : 'text-gray-400 dark:text-gray-500'
            )
          }
        >
          <Icon className="h-4 w-4" />
          <span>{label}</span>
        </NavLink>
      ))}
    </nav>
  )
}
