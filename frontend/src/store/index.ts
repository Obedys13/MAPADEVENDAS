import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { FiltrosDashboard } from '../types'

// ─── Auth Store ──────────────────────────────────────────────────────────────
interface AuthState {
  token: string | null
  usuario: string | null
  perfil: string | null
  isAuthenticated: boolean
  login: (token: string, usuario: string, perfil: string) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      usuario: null,
      perfil: null,
      isAuthenticated: false,
      login: (token, usuario, perfil) =>
        set({ token, usuario, perfil, isAuthenticated: true }),
      logout: () =>
        set({ token: null, usuario: null, perfil: null, isAuthenticated: false }),
    }),
    { name: 'gdm-auth' }
  )
)

// ─── Theme Store ─────────────────────────────────────────────────────────────
interface ThemeState {
  theme: 'light' | 'dark'
  toggleTheme: () => void
  setTheme: (t: 'light' | 'dark') => void
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: 'light',
      toggleTheme: () =>
        set((s) => {
          const next = s.theme === 'light' ? 'dark' : 'light'
          if (next === 'dark') document.documentElement.classList.add('dark')
          else document.documentElement.classList.remove('dark')
          return { theme: next }
        }),
      setTheme: (t) => {
        if (t === 'dark') document.documentElement.classList.add('dark')
        else document.documentElement.classList.remove('dark')
        set({ theme: t })
      },
    }),
    { name: 'gdm-theme' }
  )
)

// ─── Filter Store ─────────────────────────────────────────────────────────────
interface FilterState {
  filtros: FiltrosDashboard
  setFiltros: (f: Partial<FiltrosDashboard>) => void
  clearFiltros: () => void
}

const defaultFiltros: FiltrosDashboard = {}

export const useFilterStore = create<FilterState>()((set) => ({
  filtros: defaultFiltros,
  setFiltros: (f) => set((s) => ({ filtros: { ...s.filtros, ...f } })),
  clearFiltros: () => set({ filtros: defaultFiltros }),
}))
