import { Menu, Sun, Moon, RefreshCw } from 'lucide-react'
import { useThemeStore } from '../../store'
import { Button } from '../ui/Button'

interface TopbarProps {
  onMenuClick: () => void
  isMobile: boolean
}

export function Topbar({ onMenuClick, isMobile }: TopbarProps) {
  const { theme, toggleTheme } = useThemeStore()

  return (
    <header className="h-10 flex items-center gap-2 px-3 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shrink-0">
      {isMobile && (
        <Button variant="ghost" size="xs" onClick={onMenuClick} aria-label="Menu">
          <Menu className="h-4 w-4" />
        </Button>
      )}

      <div className="flex-1" />

      <Button
        variant="ghost"
        size="xs"
        onClick={toggleTheme}
        aria-label={theme === 'light' ? 'Ativar tema escuro' : 'Ativar tema claro'}
      >
        {theme === 'light' ? <Moon className="h-3.5 w-3.5" /> : <Sun className="h-3.5 w-3.5" />}
      </Button>
    </header>
  )
}
