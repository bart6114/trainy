import { ComposedChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import type { PainEvent } from '@/types'

interface PainTimelineChartProps {
  data: PainEvent[]
}

// Color mapping for pain locations
const LOCATION_COLORS: Record<string, string> = {
  knee: '#ef4444',
  back: '#f97316',
  shoulder: '#eab308',
  hip: '#22c55e',
  ankle: '#3b82f6',
  neck: '#8b5cf6',
  foot: '#ec4899',
  wrist: '#06b6d4',
  other: '#6b7280',
}

function getLocationColor(location: string | null): string {
  if (!location) return LOCATION_COLORS.other
  const normalized = location.toLowerCase()
  return LOCATION_COLORS[normalized] || LOCATION_COLORS.other
}

type ChartDataPoint = PainEvent & { timestamp: number }

interface CustomTooltipProps {
  active?: boolean
  payload?: Array<{ payload: PainEvent & { timestamp: number } }>
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || !payload[0]) return null

  const event = payload[0].payload

  return (
    <div className="bg-background border rounded-lg shadow-lg p-3 text-sm">
      <p className="font-semibold mb-2">{event.date}</p>
      <div className="space-y-1">
        <div className="flex justify-between gap-4">
          <span className="text-muted-foreground">Location:</span>
          <span className="font-medium capitalize">{event.pain_location || 'Unknown'}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-muted-foreground">Severity:</span>
          <span className="font-medium">{event.pain_severity}/10</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-muted-foreground">Activity:</span>
          <span className="font-medium capitalize">{event.activity_type}</span>
        </div>
        {event.activity_title && (
          <div className="text-xs text-muted-foreground mt-1">
            {event.activity_title}
          </div>
        )}
      </div>
    </div>
  )
}

export function PainTimelineChart({ data }: PainTimelineChartProps) {
  if (data.length === 0) {
    return (
      <div className="h-[250px] flex items-center justify-center text-muted-foreground">
        No pain events to display
      </div>
    )
  }

  // Convert dates to timestamps for chart
  const chartData: ChartDataPoint[] = data.map((event) => ({
    ...event,
    timestamp: new Date(event.date).getTime(),
  }))

  // Group events by location and sort chronologically
  const groupedByLocation = chartData.reduce<Record<string, ChartDataPoint[]>>((acc, event) => {
    const location = event.pain_location || 'other'
    if (!acc[location]) {
      acc[location] = []
    }
    acc[location].push(event)
    return acc
  }, {})

  // Sort each group by timestamp
  Object.values(groupedByLocation).forEach(group => {
    group.sort((a, b) => a.timestamp - b.timestamp)
  })

  // Get unique locations for legend and lines
  const uniqueLocations = Object.keys(groupedByLocation)

  return (
    <div className="space-y-2">
      <div className="h-[250px]">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart margin={{ top: 20, right: 30, left: 10, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="timestamp"
              type="number"
              domain={['dataMin', 'dataMax']}
              tickFormatter={(ts) => {
                const d = new Date(ts)
                return `${d.getMonth() + 1}/${d.getDate()}`
              }}
              tick={{ fontSize: 11 }}
              stroke="#9ca3af"
              axisLine={{ stroke: '#d1d5db' }}
              allowDuplicatedCategory={false}
            />
            <YAxis
              dataKey="pain_severity"
              type="number"
              domain={[0, 10]}
              ticks={[0, 2, 4, 6, 8, 10]}
              tick={{ fontSize: 11 }}
              stroke="#9ca3af"
              axisLine={{ stroke: '#d1d5db' }}
              label={{
                value: 'Severity',
                angle: -90,
                position: 'insideLeft',
                style: { fontSize: 12, fill: '#6b7280' },
                offset: 0,
              }}
            />
            <Tooltip content={<CustomTooltip />} />
            {/* Render a line + scatter for each location group */}
            {uniqueLocations.map((location) => {
              const locationData = groupedByLocation[location]
              const color = getLocationColor(location)
              return (
                <Line
                  key={`line-${location}`}
                  data={locationData}
                  dataKey="pain_severity"
                  stroke={color}
                  strokeWidth={2}
                  strokeOpacity={0.6}
                  dot={{ fill: color, r: 5, strokeWidth: 0 }}
                  activeDot={{ r: 7, fill: color }}
                  connectNulls={false}
                  isAnimationActive={false}
                />
              )
            })}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      {/* Legend */}
      <div className="flex flex-wrap gap-3 justify-center text-xs">
        {uniqueLocations.map((location) => (
          <div key={location} className="flex items-center gap-1">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: getLocationColor(location) }}
            />
            <span className="capitalize">{location}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
