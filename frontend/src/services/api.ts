import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || '/api'

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Inject auth token
api.interceptors.request.use((config) => {
  try {
    const stored = localStorage.getItem('gdm-auth')
    if (stored) {
      const { state } = JSON.parse(stored)
      if (state?.token) {
        config.headers.Authorization = `Bearer ${state.token}`
      }
    }
  } catch {}
  return config
})

// Auth
export const authApi = {
  login: (password: string) =>
    api.post('/auth/login', { password }).then((r) => r.data),
}

// Dashboard
export const dashboardApi = {
  getKpis: (params: Record<string, string | undefined>) =>
    api.get('/dashboard/kpis', { params }).then((r) => r.data),
  getGraficos: (params: Record<string, string | undefined>) =>
    api.get('/dashboard/graficos', { params }).then((r) => r.data),
  getResumoVendedor: (params: Record<string, string | undefined>) =>
    api.get('/dashboard/resumo/vendedor', { params }).then((r) => r.data),
  getOpcoesFiltros: () =>
    api.get('/dashboard/filtros/opcoes').then((r) => r.data),
}

// Uploads
export const uploadsApi = {
  preview: (tipo: string, file: File, dataReferencia?: string) => {
    const fd = new FormData()
    fd.append('arquivo', file)
    if (dataReferencia) fd.append('data_referencia', dataReferencia)
    return api.post(`/uploads/${tipo}/preview`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r) => r.data)
  },
  confirmar: (tipo: string, uploadId: string, file: File, dataReferencia?: string, substituir = false) => {
    const fd = new FormData()
    fd.append('upload_id', uploadId)
    fd.append('arquivo', file)
    if (dataReferencia) fd.append('data_referencia', dataReferencia)
    fd.append('substituir', String(substituir))
    return api.post(`/uploads/${tipo}/confirmar`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r) => r.data)
  },
  historico: (tipo?: string, limit = 50) =>
    api.get('/uploads/historico', { params: { tipo, limit } }).then((r) => r.data),
  status: (uploadId: string) =>
    api.get(`/uploads/${uploadId}/status`).then((r) => r.data),
}

// Análises
export const analisesApi = {
  insights:    (params: Record<string, string | undefined>) =>
    api.get('/analises/insights',    { params }).then((r) => r.data),
  ruptura:     (params: Record<string, string | undefined>) =>
    api.get('/analises/ruptura',     { params }).then((r) => r.data),
  dde:         (dataReferencia?: string) =>
    api.get('/analises/dde', { params: { data_referencia: dataReferencia } }).then((r) => r.data),
  logistica:   (params: Record<string, string | undefined>) =>
    api.get('/analises/logistica',   { params }).then((r) => r.data),
  margem:      (params: Record<string, string | undefined>) =>
    api.get('/analises/margem',      { params }).then((r) => r.data),
  categorias:  (params: Record<string, string | undefined>) =>
    api.get('/analises/categorias',  { params }).then((r) => r.data),
  supervisores:(params: Record<string, string | undefined>) =>
    api.get('/analises/supervisores',{ params }).then((r) => r.data),
  redes:       (params: Record<string, string | undefined>) =>
    api.get('/analises/redes',       { params }).then((r) => r.data),
  precos:      (params: Record<string, string | undefined>) =>
    api.get('/analises/precos',      { params }).then((r) => r.data),
}

function getStoredToken(): string {
  try {
    const stored = localStorage.getItem('gdm-auth')
    if (stored) {
      const { state } = JSON.parse(stored)
      return state?.token || ''
    }
  } catch {}
  return ''
}

// Relatórios
export const relatoriosApi = {
  diario: (dataReferencia?: string) =>
    api.get('/relatorios/diario', { params: { data_referencia: dataReferencia } }).then((r) => r.data),
  exportCsv: (params: Record<string, string | undefined>) => {
    const clean = Object.fromEntries(Object.entries(params).filter(([, v]) => v != null)) as Record<string, string>
    clean.token = getStoredToken()
    const url = `${BASE_URL}/relatorios/export/csv?${new URLSearchParams(clean)}`
    window.open(url, '_blank')
  },
  exportExcel: (params: Record<string, string | undefined>) => {
    const clean = Object.fromEntries(Object.entries(params).filter(([, v]) => v != null)) as Record<string, string>
    clean.token = getStoredToken()
    const url = `${BASE_URL}/relatorios/export/excel?${new URLSearchParams(clean)}`
    window.open(url, '_blank')
  },
}

// Configurações
export const configApi = {
  getParametros: () => api.get('/configuracoes/parametros').then((r) => r.data),
  setParametro: (chave: string, valor: string) =>
    api.put('/configuracoes/parametros', { chave, valor }).then((r) => r.data),
  getMetas: (ano?: number, mes?: number) =>
    api.get('/configuracoes/metas', { params: { ano, mes } }).then((r) => r.data),
  criarMeta: (data: Record<string, unknown>) =>
    api.post('/configuracoes/metas', data).then((r) => r.data),
  deletarMeta: (id: string) =>
    api.delete(`/configuracoes/metas/${id}`).then((r) => r.data),
  getLogistica: () => api.get('/configuracoes/logistica').then((r) => r.data),
  salvarLogistica: (data: Record<string, unknown>) =>
    api.post('/configuracoes/logistica', data).then((r) => r.data),
  getBasesVigentes: () => api.get('/configuracoes/bases-vigentes').then((r) => r.data),
  getHistoricoUploads: () => api.get('/configuracoes/historico-uploads').then((r) => r.data),
}
