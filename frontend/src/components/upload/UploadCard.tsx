import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, CheckCircle, AlertCircle, Clock, Loader2, Eye, RefreshCw, Download, History } from 'lucide-react'
import { Button } from '../ui/Button'
import { StatusBadge } from '../ui/Badge'
import { uploadsApi } from '../../services/api'
import { formatDatetime } from '../../utils/formatters'
import type { UploadHistorico, UploadPreview } from '../../types'
import { cn } from '../../utils/cn'

interface UploadCardProps {
  tipo: string
  nome: string
  descricao: string
  lastUpload?: UploadHistorico
  isDaily?: boolean
  onSuccess?: () => void
}

export function UploadCard({ tipo, nome, descricao, lastUpload, isDaily = false, onSuccess }: UploadCardProps) {
  const [step, setStep] = useState<'idle' | 'preview' | 'confirming' | 'done'>('idle')
  const [preview, setPreview] = useState<UploadPreview | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [dataRef, setDataRef] = useState(new Date().toISOString().split('T')[0])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [substituir, setSubstituir] = useState(false)
  const [result, setResult] = useState<string>('')

  const onDrop = useCallback(async (accepted: File[]) => {
    if (!accepted.length) return
    const f = accepted[0]
    setFile(f)
    setLoading(true)
    setError('')
    try {
      const prev = await uploadsApi.preview(tipo, f, dataRef)
      setPreview(prev)
      setStep('preview')
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Erro ao processar arquivo.')
    } finally {
      setLoading(false)
    }
  }, [tipo, dataRef])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'] },
    maxFiles: 1,
    disabled: loading || step === 'confirming',
  })

  const handleConfirm = async () => {
    if (!preview || !file) return
    setLoading(true)
    setStep('confirming')
    try {
      const res = await uploadsApi.confirmar(tipo, preview.upload_id, file, dataRef, substituir)
      setResult(res.mensagem || 'Importação concluída.')
      setStep('done')
      onSuccess?.()
    } catch (e: any) {
      const msg = e?.response?.data?.detail || 'Erro na importação.'
      if (e?.response?.data?.ja_existe) {
        setSubstituir(true)
        setError('Já existe upload para esta data. Ative "substituir" e confirme.')
      } else {
        setError(msg)
      }
      setStep('preview')
    } finally {
      setLoading(false)
    }
  }

  const reset = () => {
    setStep('idle')
    setPreview(null)
    setFile(null)
    setError('')
    setResult('')
    setSubstituir(false)
  }

  return (
    <div className="card p-3 flex flex-col gap-2">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">{nome}</h3>
          <p className="text-2xs text-gray-400 mt-0.5">{descricao}</p>
        </div>
        {lastUpload && <StatusBadge status={lastUpload.status} />}
      </div>

      {lastUpload && (
        <div className="text-2xs text-gray-400 flex items-center gap-3">
          <span>Último: {formatDatetime(lastUpload.data_hora_upload)}</span>
          {lastUpload.total_registros && <span>{lastUpload.total_registros} registros</span>}
        </div>
      )}

      {/* Data de referência */}
      <div className="flex items-center gap-2">
        <label className="text-2xs text-gray-500 shrink-0">Data referência:</label>
        <input
          type="date"
          value={dataRef}
          onChange={(e) => setDataRef(e.target.value)}
          className="h-6 text-xs border border-gray-200 dark:border-gray-700 rounded px-1.5 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 focus:outline-none"
        />
      </div>

      {step === 'idle' && (
        <div
          {...getRootProps()}
          className={cn(
            'border-2 border-dashed rounded-md p-4 text-center cursor-pointer transition-colors',
            isDragActive
              ? 'border-brand-700 bg-brand-50 dark:border-accent-500 dark:bg-accent-900/10'
              : 'border-gray-200 dark:border-gray-700 hover:border-brand-400 dark:hover:border-accent-600'
          )}
        >
          <input {...getInputProps()} />
          {loading ? (
            <Loader2 className="h-6 w-6 animate-spin mx-auto text-gray-400" />
          ) : (
            <>
              <Upload className="h-5 w-5 mx-auto text-gray-300 dark:text-gray-600 mb-1" />
              <p className="text-xs text-gray-400">
                {isDragActive ? 'Solte o arquivo aqui' : 'Arraste o .xlsx ou clique para selecionar'}
              </p>
            </>
          )}
        </div>
      )}

      {error && (
        <div className="flex items-start gap-1.5 p-2 rounded bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
          <AlertCircle className="h-3.5 w-3.5 text-red-500 shrink-0 mt-0.5" />
          <p className="text-2xs text-red-700 dark:text-red-400">{error}</p>
        </div>
      )}

      {step === 'preview' && preview && (
        <div className="flex flex-col gap-2 animate-fade-in">
          <div className="flex items-center gap-2 text-2xs">
            <span className="text-gray-500">Arquivo:</span>
            <span className="font-medium text-gray-700 dark:text-gray-300">{file?.name}</span>
          </div>
          <div className="grid grid-cols-2 gap-1.5 text-2xs">
            <div className="flex justify-between">
              <span className="text-gray-400">Registros:</span>
              <span className="font-medium">{preview.total_registros}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Pode importar:</span>
              <span className={preview.pode_importar ? 'text-green-600' : 'text-red-500'}>
                {preview.pode_importar ? 'Sim' : 'Não'}
              </span>
            </div>
          </div>

          {preview.colunas_ausentes.length > 0 && (
            <div className="p-1.5 rounded bg-red-50 dark:bg-red-900/20 border border-red-200">
              <p className="text-2xs font-medium text-red-700">Colunas ausentes:</p>
              <p className="text-2xs text-red-600">{preview.colunas_ausentes.join(', ')}</p>
            </div>
          )}
          {preview.avisos.length > 0 && (
            <div className="p-1.5 rounded bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200">
              {preview.avisos.map((a, i) => (
                <p key={i} className="text-2xs text-yellow-700">{a}</p>
              ))}
            </div>
          )}

          {/* Preview rows */}
          {preview.preview_linhas.length > 0 && (
            <div className="overflow-x-auto border border-gray-100 dark:border-gray-800 rounded">
              <table className="text-2xs w-full">
                <thead className="bg-gray-50 dark:bg-gray-800">
                  <tr>
                    {Object.keys(preview.preview_linhas[0]).slice(0, 8).map((h) => (
                      <th key={h} className="px-1.5 py-1 text-left font-medium text-gray-500 whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.preview_linhas.map((row, i) => (
                    <tr key={i} className="border-t border-gray-100 dark:border-gray-800">
                      {Object.values(row).slice(0, 8).map((v, j) => (
                        <td key={j} className="px-1.5 py-0.5 text-gray-600 dark:text-gray-400 whitespace-nowrap max-w-24 truncate">
                          {String(v ?? '—')}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {isDaily ? (
            <p className="text-2xs text-blue-600 dark:text-blue-400">
              Substituição automática do upload do mesmo dia.
            </p>
          ) : (
            <div className="flex items-center gap-2">
              <label className="flex items-center gap-1.5 text-2xs text-gray-500 cursor-pointer">
                <input
                  type="checkbox"
                  checked={substituir}
                  onChange={(e) => setSubstituir(e.target.checked)}
                  className="rounded"
                />
                Substituir versão anterior
              </label>
            </div>
          )}

          <div className="flex items-center gap-2">
            {preview.pode_importar && (
              <Button variant="primary" size="sm" onClick={handleConfirm} loading={loading}>
                Confirmar Importação
              </Button>
            )}
            <Button variant="ghost" size="sm" onClick={reset}>Cancelar</Button>
          </div>
        </div>
      )}

      {step === 'done' && (
        <div className="flex flex-col gap-2 animate-fade-in">
          <div className="flex items-center gap-2 p-2 rounded bg-green-50 dark:bg-green-900/20 border border-green-200">
            <CheckCircle className="h-4 w-4 text-green-600 shrink-0" />
            <p className="text-xs text-green-700 dark:text-green-400">{result}</p>
          </div>
          <Button variant="ghost" size="sm" onClick={reset}>Novo Upload</Button>
        </div>
      )}
    </div>
  )
}
