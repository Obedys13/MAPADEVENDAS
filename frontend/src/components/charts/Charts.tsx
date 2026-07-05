import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, Cell, PieChart, Pie,
} from 'recharts'
import { useThemeStore } from '../../store'
import { shortBRL, formatBRL, formatNumber } from '../../utils/formatters'
import type { GraficoItem } from '../../types'

const COLORS_LIGHT = ['#004400', '#006600', '#008800', '#22aa22', '#44cc44', '#66dd66', '#88ee88', '#aaffaa', '#ccffcc']
const COLORS_DARK = ['#ed5600', '#ff7733', '#ff9966', '#ffbb99', '#ffddcc', '#ff6644', '#ff4422', '#cc3300', '#aa2200']

function useChartColors() {
  const theme = useThemeStore((s) => s.theme)
  return theme === 'dark' ? COLORS_DARK : COLORS_LIGHT
}

function useTickStyle() {
  const theme = useThemeStore((s) => s.theme)
  return { fill: theme === 'dark' ? '#9ca3af' : '#6b7280', fontSize: 10 }
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="card p-2 text-xs shadow-card-md">
      <p className="font-semibold mb-1 text-gray-700 dark:text-gray-200">{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} style={{ color: p.color }} className="tabular-nums">
          {p.name}: {typeof p.value === 'number' ? formatBRL(p.value) : p.value}
        </p>
      ))}
    </div>
  )
}

interface ChartWrapperProps {
  title: string
  children: React.ReactNode
  height?: number
}

export function ChartWrapper({ title, children, height = 220 }: ChartWrapperProps) {
  return (
    <div className="card p-3">
      <h4 className="text-xs font-semibold text-gray-700 dark:text-gray-200 mb-2">{title}</h4>
      <div style={{ height }}>{children}</div>
    </div>
  )
}

interface BarProps {
  data: GraficoItem[]
  title: string
  dataKey?: string
  layout?: 'vertical' | 'horizontal'
  height?: number
  formatValue?: (v: number) => string
}

export function SimpleBarChart({
  data,
  title,
  dataKey = 'valor',
  layout = 'horizontal',
  height = 220,
  formatValue = shortBRL,
}: BarProps) {
  const colors = useChartColors()
  const tickStyle = useTickStyle()

  if (!data?.length) return (
    <ChartWrapper title={title} height={height}>
      <div className="flex items-center justify-center h-full text-xs text-gray-400">Sem dados</div>
    </ChartWrapper>
  )

  return (
    <ChartWrapper title={title} height={height}>
      <ResponsiveContainer width="100%" height="100%">
        {layout === 'horizontal' ? (
          <BarChart data={data} margin={{ top: 2, right: 8, bottom: 2, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" strokeOpacity={0.5} />
            <XAxis dataKey="label" tick={tickStyle} tickLine={false} axisLine={false} />
            <YAxis tickFormatter={formatValue} tick={tickStyle} tickLine={false} axisLine={false} width={50} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey={dataKey} radius={[2, 2, 0, 0]}>
              {data.map((_, i) => <Cell key={i} fill={colors[i % colors.length]} />)}
            </Bar>
          </BarChart>
        ) : (
          <BarChart data={data} layout="vertical" margin={{ top: 2, right: 8, bottom: 2, left: 80 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" strokeOpacity={0.5} horizontal={false} />
            <XAxis type="number" tickFormatter={formatValue} tick={tickStyle} tickLine={false} axisLine={false} />
            <YAxis dataKey="label" type="category" tick={tickStyle} tickLine={false} axisLine={false} width={75} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey={dataKey} radius={[0, 2, 2, 0]}>
              {data.map((_, i) => <Cell key={i} fill={colors[i % colors.length]} />)}
            </Bar>
          </BarChart>
        )}
      </ResponsiveContainer>
    </ChartWrapper>
  )
}

interface LineProps {
  data: GraficoItem[]
  title: string
  height?: number
}

export function SimpleLineChart({ data, title, height = 220 }: LineProps) {
  const colors = useChartColors()
  const tickStyle = useTickStyle()

  if (!data?.length) return (
    <ChartWrapper title={title} height={height}>
      <div className="flex items-center justify-center h-full text-xs text-gray-400">Sem dados</div>
    </ChartWrapper>
  )

  return (
    <ChartWrapper title={title} height={height}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 2, right: 8, bottom: 2, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" strokeOpacity={0.5} />
          <XAxis dataKey="label" tick={tickStyle} tickLine={false} axisLine={false} />
          <YAxis tickFormatter={shortBRL} tick={tickStyle} tickLine={false} axisLine={false} width={50} />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize: 10 }} />
          <Line type="monotone" dataKey="valor" name="Faturamento" stroke={colors[0]} strokeWidth={1.5} dot={false} />
          {data[0]?.secundario !== undefined && (
            <Line type="monotone" dataKey="secundario" name="Margem" stroke={colors[2]} strokeWidth={1.5} dot={false} strokeDasharray="4 2" />
          )}
        </LineChart>
      </ResponsiveContainer>
    </ChartWrapper>
  )
}
