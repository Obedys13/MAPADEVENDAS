import { cn } from '../../utils/cn'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface KpiCardProps {
  title: string
  value: string
  subtitle?: string
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
  status?: 'positive' | 'negative' | 'warning' | 'neutral'
  icon?: React.ReactNode
  className?: string
  compact?: boolean
}

export function KpiCard({
  title,
  value,
  subtitle,
  trend,
  trendValue,
  status = 'neutral',
  icon,
  className,
  compact = false,
}: KpiCardProps) {
  return (
    <div
      className={cn(
        'card flex flex-col gap-1',
        compact ? 'p-2.5' : 'p-3',
        className
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-2xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide truncate">
          {title}
        </span>
        {icon && (
          <span className="text-gray-400 dark:text-gray-500 shrink-0">{icon}</span>
        )}
      </div>

      <div className="flex items-end justify-between gap-1">
        <span
          className={cn('font-semibold tabular-nums', compact ? 'text-lg' : 'text-xl', {
            'text-green-700 dark:text-green-400': status === 'positive',
            'text-red-600 dark:text-red-400': status === 'negative',
            'text-yellow-600 dark:text-yellow-400': status === 'warning',
            'text-gray-900 dark:text-gray-100': status === 'neutral',
          })}
        >
          {value}
        </span>

        {trend && trendValue && (
          <div
            className={cn('flex items-center gap-0.5 text-2xs font-medium shrink-0 mb-0.5', {
              'text-green-600 dark:text-green-400': trend === 'up',
              'text-red-500 dark:text-red-400': trend === 'down',
              'text-gray-400': trend === 'neutral',
            })}
          >
            {trend === 'up' ? (
              <TrendingUp className="h-3 w-3" />
            ) : trend === 'down' ? (
              <TrendingDown className="h-3 w-3" />
            ) : (
              <Minus className="h-3 w-3" />
            )}
            {trendValue}
          </div>
        )}
      </div>

      {subtitle && (
        <span className="text-2xs text-gray-400 dark:text-gray-500">{subtitle}</span>
      )}
    </div>
  )
}

interface KpiGroupProps {
  title: string
  children: React.ReactNode
  columns?: 2 | 3 | 4 | 5
}

export function KpiGroup({ title, children, columns = 4 }: KpiGroupProps) {
  return (
    <div>
      <h4 className="text-2xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-1.5 px-0.5">
        {title}
      </h4>
      <div
        className={cn('grid gap-2', {
          'grid-cols-2': columns === 2,
          'grid-cols-2 sm:grid-cols-3': columns === 3,
          'grid-cols-2 sm:grid-cols-4': columns === 4,
          'grid-cols-2 sm:grid-cols-3 lg:grid-cols-5': columns === 5,
        })}
      >
        {children}
      </div>
    </div>
  )
}
