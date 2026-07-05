import { cn } from '../../utils/cn'

interface BadgeProps {
  variant?: 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'brand'
  children: React.ReactNode
  className?: string
}

export function Badge({ variant = 'neutral', children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded px-1.5 py-0.5 text-2xs font-medium',
        {
          'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400': variant === 'success',
          'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400': variant === 'warning',
          'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400': variant === 'danger',
          'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400': variant === 'info',
          'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300': variant === 'neutral',
          'bg-brand-100 text-brand-800 dark:bg-accent-900/30 dark:text-accent-400': variant === 'brand',
        },
        className
      )}
    >
      {children}
    </span>
  )
}

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; variant: BadgeProps['variant'] }> = {
    concluido: { label: 'Concluído', variant: 'success' },
    processando: { label: 'Processando', variant: 'info' },
    pendente: { label: 'Pendente', variant: 'neutral' },
    erro: { label: 'Erro', variant: 'danger' },
    aguardando_confirmacao: { label: 'Aguardando', variant: 'warning' },
    viavel: { label: 'Viável', variant: 'success' },
    aumentar_valor: { label: 'Aumentar Valor', variant: 'warning' },
    aumentar_peso: { label: 'Aumentar Peso', variant: 'warning' },
    sem_parametro: { label: 'Sem Parâmetro', variant: 'neutral' },
    acima: { label: 'Acima', variant: 'success' },
    abaixo: { label: 'Abaixo', variant: 'danger' },
  }
  const info = map[status] ?? { label: status, variant: 'neutral' }
  return <Badge variant={info.variant}>{info.label}</Badge>
}
