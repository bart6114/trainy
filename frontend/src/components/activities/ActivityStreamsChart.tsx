import { useState, useMemo } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import type { ActivityStreams } from '@/types'

interface ActivityStreamsChartProps {
  streams: ActivityStreams
  activityType: string
  hoveredIndex: number | null
  onHoverIndexChange: (index: number | null) => void
}

interface StreamConfig {
  key: keyof Pick<ActivityStreams, 'heart_rate' | 'power' | 'cadence' | 'speed' | 'elevation'>
  label: string
  unit: string
  color: string
  formatter: (value: number | null) => string
}

const STREAM_CONFIGS: StreamConfig[] = [
  {
    key: 'heart_rate',
    label: 'Heart Rate',
    unit: 'bpm',
    color: '#ef4444',
    formatter: (v) => (v !== null ? `${Math.round(v)} bpm` : '-'),
  },
  {
    key: 'power',
    label: 'Power',
    unit: 'W',
    color: '#8b5cf6',
    formatter: (v) => (v !== null ? `${Math.round(v)} W` : '-'),
  },
  {
    key: 'cadence',
    label: 'Cadence',
    unit: 'rpm',
    color: '#06b6d4',
    formatter: (v) => (v !== null ? `${Math.round(v)} rpm` : '-'),
  },
  {
    key: 'speed',
    label: 'Speed',
    unit: 'km/h',
    color: '#22c55e',
    formatter: (v) => (v !== null ? `${(v * 3.6).toFixed(1)} km/h` : '-'),
  },
  {
    key: 'elevation',
    label: 'Elevation',
    unit: 'm',
    color: '#f59e0b',
    formatter: (v) => (v !== null ? `${Math.round(v)} m` : '-'),
  },
]

function formatTimeAxis(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  if (hours > 0) {
    return `${hours}:${mins.toString().padStart(2, '0')}`
  }
  return `${mins}m`
}

function formatTimeFull(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  if (hours > 0) {
    return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

interface ChartDataPoint {
  index: number
  timestamp: number
  heart_rate: number | null
  power: number | null
  cadence: number | null
  speed: number | null
  elevation: number | null
  distance: number
}

interface StreamChartProps {
  data: ChartDataPoint[]
  config: StreamConfig
  hoveredIndex: number | null
  onHover: (index: number | null) => void
  domain: [number, number]
}

function StreamChart({ data, config, hoveredIndex, onHover, domain }: StreamChartProps) {
  const yDomain = useMemo(() => {
    const values = data.map((d) => d[config.key]).filter((v): v is number => v !== null)
    if (values.length === 0) return [0, 100] as [number, number]
    const min = Math.min(...values)
    const max = Math.max(...values)
    const padding = (max - min) * 0.1 || 10
    return [Math.max(0, min - padding), max + padding] as [number, number]
  }, [data, config.key])

  return (
    <div className="h-[100px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={data}
          margin={{ top: 5, right: 10, left: 0, bottom: 5 }}
          onMouseMove={(state) => {
            if (state?.activeTooltipIndex !== undefined) {
              onHover(state.activeTooltipIndex)
            }
          }}
          onMouseLeave={() => onHover(null)}
        >
          <XAxis
            dataKey="timestamp"
            type="number"
            domain={domain}
            tickFormatter={formatTimeAxis}
            tick={{ fontSize: 10 }}
            stroke="#9ca3af"
            axisLine={false}
            tickLine={false}
            hide
          />
          <YAxis
            domain={yDomain}
            tick={{ fontSize: 10 }}
            stroke="#9ca3af"
            axisLine={false}
            tickLine={false}
            width={45}
            tickFormatter={(v) => Math.round(v).toString()}
          />
          <Tooltip
            content={() => null}
            cursor={{ stroke: '#6b7280', strokeWidth: 1 }}
          />
          <Line
            type="monotone"
            dataKey={config.key}
            stroke={config.color}
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
            connectNulls
          />
          {hoveredIndex !== null && data[hoveredIndex] && (
            <ReferenceLine
              x={data[hoveredIndex].timestamp}
              stroke="#6b7280"
              strokeDasharray="3 3"
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export function ActivityStreamsChart({
  streams,
  activityType,
  hoveredIndex,
  onHoverIndexChange,
}: ActivityStreamsChartProps) {
  const isRunning = activityType === 'run'

  const availableStreams = STREAM_CONFIGS.filter((config) => {
    const data = streams[config.key]
    return data && data.some((v) => v !== null)
  })

  const [enabledStreams, setEnabledStreams] = useState<Set<string>>(() => {
    return new Set(availableStreams.map((s) => s.key))
  })

  const chartData: ChartDataPoint[] = useMemo(() => {
    return streams.timestamps.map((timestamp, index) => ({
      index,
      timestamp,
      heart_rate: streams.heart_rate?.[index] ?? null,
      power: streams.power?.[index] ?? null,
      cadence: streams.cadence?.[index] ?? null,
      speed: streams.speed?.[index] ?? null,
      elevation: streams.elevation?.[index] ?? null,
      distance: streams.distance[index] ?? 0,
    }))
  }, [streams])

  const timeDomain: [number, number] = useMemo(() => {
    if (streams.timestamps.length === 0) return [0, 0]
    return [streams.timestamps[0], streams.timestamps[streams.timestamps.length - 1]]
  }, [streams.timestamps])

  const toggleStream = (key: string) => {
    setEnabledStreams((prev) => {
      const next = new Set(prev)
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
      return next
    })
  }

  const hoveredData = hoveredIndex !== null ? chartData[hoveredIndex] : null

  if (availableStreams.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-muted-foreground">
        No stream data available for this activity
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex flex-wrap gap-4">
        {availableStreams.map((config) => (
          <div key={config.key} className="flex items-center space-x-2">
            <Switch
              id={config.key}
              checked={enabledStreams.has(config.key)}
              onCheckedChange={() => toggleStream(config.key)}
            />
            <Label
              htmlFor={config.key}
              className="text-sm cursor-pointer"
              style={{ color: config.color }}
            >
              {config.label}
            </Label>
          </div>
        ))}
      </div>

      {/* Hover info bar */}
      <div className="h-8 px-2 bg-muted/50 rounded flex items-center gap-4 text-sm">
        {hoveredData ? (
          <>
            <span className="text-muted-foreground">
              {formatTimeFull(hoveredData.timestamp)}
            </span>
            <span className="text-muted-foreground">
              {(hoveredData.distance / 1000).toFixed(2)} km
            </span>
            {availableStreams
              .filter((config) => enabledStreams.has(config.key))
              .map((config) => (
                <span key={config.key} style={{ color: config.color }}>
                  {config.formatter(hoveredData[config.key])}
                </span>
              ))}
          </>
        ) : (
          <span className="text-muted-foreground">Hover over charts to see values</span>
        )}
      </div>

      {/* Stacked charts */}
      <div className="space-y-2">
        {availableStreams
          .filter((config) => enabledStreams.has(config.key))
          .map((config) => {
            const currentValue = hoveredData ? hoveredData[config.key] : null
            const unit = isRunning && config.key === 'cadence' ? 'spm' : config.unit
            return (
              <div key={config.key} className="border rounded-lg p-2">
                <div className="flex items-center justify-between mb-1 px-1">
                  <span className="text-xs font-medium" style={{ color: config.color }}>
                    {config.label}
                  </span>
                  <span
                    className="text-xs font-medium"
                    style={{ color: currentValue !== null ? config.color : undefined }}
                  >
                    {currentValue !== null
                      ? config.key === 'speed'
                        ? `${(currentValue * 3.6).toFixed(1)} ${unit}`
                        : `${Math.round(currentValue)} ${unit}`
                      : unit}
                  </span>
                </div>
                <StreamChart
                  data={chartData}
                  config={config}
                  hoveredIndex={hoveredIndex}
                  onHover={onHoverIndexChange}
                  domain={timeDomain}
                />
              </div>
            )
          })}
      </div>
    </div>
  )
}
