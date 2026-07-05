import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Loader2 } from 'lucide-react'
import { authApi } from '../services/api'
import { useAuthStore } from '../store'

export default function Login() {
  const [password, setPassword] = useState('')
  const [show, setShow] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const login = useAuthStore((s) => s.login)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!password.trim()) return
    setLoading(true)
    setError('')
    try {
      const data = await authApi.login(password)
      login(data.access_token, data.usuario, data.perfil)
      navigate('/dashboard')
    } catch {
      setError('Senha incorreta. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="min-h-dvh flex items-center justify-center p-4"
      style={{ background: 'linear-gradient(135deg, #001a00 0%, #004400 50%, #002200 100%)' }}
    >
      {/* Logo de fundo sutil */}
      <div
        className="absolute inset-0 opacity-5"
        style={{
          backgroundImage: 'radial-gradient(circle at 30% 40%, #004400 0%, transparent 50%), radial-gradient(circle at 70% 70%, #006600 0%, transparent 50%)',
        }}
      />

      <div className="relative w-full max-w-sm">
        {/* Card */}
        <div
          className="rounded-lg p-8 flex flex-col items-center gap-6"
          style={{
            background: 'rgba(255, 255, 255, 0.07)',
            backdropFilter: 'blur(16px)',
            border: '1px solid rgba(255, 255, 255, 0.12)',
          }}
        >
          {/* Logo */}
          <div className="flex flex-col items-center gap-2">
            <div className="w-14 h-14 rounded-xl bg-brand-800 flex items-center justify-center shadow-lg">
              <span className="text-white text-xl font-bold tracking-tight">GDM</span>
            </div>
            <div className="text-center">
              <h1 className="text-white text-lg font-semibold leading-tight">Grupo Doce Mel</h1>
              <p className="text-white/50 text-xs mt-0.5">Sistema de Análise — Mapa de Vendas</p>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="w-full flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-white/70">Senha de acesso</label>
              <div className="relative">
                <input
                  type={show ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoFocus
                  placeholder="Digite a senha..."
                  className="w-full h-9 px-3 pr-9 rounded bg-white/10 border border-white/20 text-white text-sm placeholder-white/30 focus:outline-none focus:border-white/50 focus:ring-1 focus:ring-white/30 transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShow((s) => !s)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/70 transition-colors"
                >
                  {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {error && (
                <p className="text-red-400 text-xs mt-0.5">{error}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading || !password}
              className="w-full h-9 rounded bg-brand-700 hover:bg-brand-600 text-white text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              {loading ? 'Entrando...' : 'Entrar'}
            </button>
          </form>

          <p className="text-white/25 text-2xs">© 2026 Grupo Doce Mel</p>
        </div>
      </div>
    </div>
  )
}
