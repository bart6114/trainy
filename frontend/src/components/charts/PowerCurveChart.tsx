import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import type { PowerCurvePoint } from '@/types'

interface PowerCurveChartProps {
  data: PowerCurvePoint[]
  showWattsPerKg: boolean
}

interface CustomTooltipProps {
  active?: boolean
  payload?: Array<{ payload: PowerCurvePoint }>
  showWattsPerKg: boolean
}

function CustomTooltip({ active, payload, showWattsPerKg }: CustomTooltipProps) {
  if (!active || !payload || !payload[0]) return null

  const point = payload[0].payload
  const value = showWattsPerKg ? point.best_watts_per_kg : point.best_watts

  return (
    <div className="bg-background border rounded-lg shadow-lg p-3 text-sm">
      <p className="font-semibold mb-2">{point.duration_label}</p>
      <div className="space-y-1">
        <div className="flex justify-between gap-4">
          <span className="text-muted-foreground">
            {showWattsPerKg ? 'W/kg:' : 'Power:'}
          </span>
          <span className="font-medium">
            {value !== null ? (showWattsPerKg ? value.toFixed(2) : `${Math.round(value)} W`) : 'No data'}
          </span>
        </div>
        {point.activity_date && (
          <div className="flex justify-between gap-4 text-xs text-muted-foreground">
            <span>Date:</span>
            <span>{point.activity_date}</span>
          </div>
        )}
      </div>
    </div>
  )
}

export function PowerCurveChart({ data, showWattsPerKg }: PowerCurveChartProps) {
  const chartData = data.map((point) => ({
    ...point,
    value: showWattsPerKg ? point.best_watts_per_kg : point.best_watts,
  }))

  const hasData = chartData.some((d) => d.value !== null)

  if (!hasData) {
    return (
      <div className="h-[300px] flex items-center justify-center text-muted-foreground">
        No power data available for this period
      </div>
    )
  }

  return (
    <div className="h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 20, right: 30, left: 10, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="duration_label"
            tick={{ fontSize: 12 }}
            stroke="#9ca3af"
            axisLine={{ stroke: '#d1d5db' }}
          />
          <YAxis
            tick={{ fontSize: 11 }}
            stroke="#9ca3af"
            axisLine={{ stroke: '#d1d5db' }}
            tickFormatter={(value) => showWattsPerKg ? value.toFixed(1) : Math.round(value).toString()}
            label={{
              value: showWattsPerKg ? 'W/kg' : 'Watts',
              angle: -90,
              position: 'insideLeft',
              style: { fontSize: 12, fill: '#6b7280' },
              offset: 0,
            }}
          />
          <Tooltip content={<CustomTooltip showWattsPerKg={showWattsPerKg} />} />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#3b82f6"
            strokeWidth={2.5}
            dot={{ r: 6, fill: '#3b82f6', strokeWidth: 2, stroke: '#fff' }}
            activeDot={{ r: 8, fill: '#2563eb', strokeWidth: 2, stroke: '#fff' }}
            connectNulls={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
