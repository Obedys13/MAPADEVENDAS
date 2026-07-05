import { useState, useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { BottomNav } from './BottomNav'
import { Topbar } from './Topbar'
import { useThemeStore } from '../../store'

export function AppShell() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [isMobile, setIsMobile] = useState(false)
  const theme = useThemeStore((s) => s.theme)

  useEffect(() => {
    const stored = localStorage.getItem('gdm-theme')
    if (stored) {
      const { state } = JSON.parse(stored)
      if (state?.theme === 'dark') document.documentElement.classList.add('dark')
    }
  }, [])

  useEffect(() => {
    const check = () => {
      const mobile = window.innerWidth < 768
      setIsMobile(mobile)
      if (mobile) setSidebarOpen(false)
    }
    check()
    window.addEventListener('resize', check)
    return () => window.removeEventListener('resize', check)
  }, [])

  return (
    <div className="min-h-dvh flex bg-gray-50 dark:bg-gray-950">
      {/* Sidebar desktop */}
      {!isMobile && (
        <Sidebar open={sidebarOpen} onToggle={() => setSidebarOpen((o) => !o)} />
      )}

      {/* Mobile sidebar overlay */}
      {isMobile && sidebarOpen && (
        <>
          <div
            className="fixed inset-0 bg-black/40 z-40"
            onClick={() => setSidebarOpen(false)}
          />
          <Sidebar open mobile onToggle={() => setSidebarOpen(false)} />
        </>
      )}

      {/* Main content */}
      <div className="flex flex-col flex-1 min-w-0 min-h-dvh">
        <Topbar onMenuClick={() => setSidebarOpen((o) => !o)} isMobile={isMobile} />
        <main className="flex-1 px-3 py-3 pb-20 md:pb-3 overflow-auto">
          <Outlet />
        </main>
      </div>

      {/* Bottom nav mobile */}
      {isMobile && <BottomNav />}
    </div>
  )
}
