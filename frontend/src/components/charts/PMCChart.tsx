import { ComposedChart, Bar, Line, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, ReferenceArea } from 'recharts'
import { format, parseISO } from 'date-fns'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import type { DailyMetricsItem, ProjectedDataPoint } from '@/types'

interface PMCChartProps {
  data: DailyMetricsItem[]
  projectedData?: ProjectedDataPoint[]
  showProjection?: boolean
  onToggleProjection?: (enabled: boolean) => void
  projectionLoading?: boolean
}

// TSB Zone definitions based on TrainingPeaks standards
const TSB_ZONES = {
  OVER_FRESH: { min: 25, color: '#93c5fd', label: 'Losing Fitness' },      // Light blue
  FRESH: { min: 5, max: 25, color: '#86efac', label: 'Fresh / Race Ready' }, // Light green
  NEUTRAL: { min: -10, max: 5, color: '#e5e7eb', label: 'Grey Zone' },       // Light grey
  OPTIMAL: { min: -30, max: -10, color: '#fde68a', label: 'Optimal Training' }, // Light yellow
  HIGH_RISK: { max: -30, color: '#fecaca', label: 'High Fatigue Risk' },    // Light red
}

function getFormStatus(tsb: number | null): { label: string; color: string } {
  if (tsb === null) return { label: 'Unknown', color: 'gray' }
  if (tsb > 25) return { label: 'Transition', color: '#3b82f6' }
  if (tsb > 5) return { label: 'Fresh', color: '#22c55e' }
  if (tsb > -10) return { label: 'Neutral', color: '#6b7280' }
  if (tsb > -30) return { label: 'Training', color: '#f59e0b' }
  return { label: 'Fatigued', color: '#ef4444' }
}

interface ChartDataPoint {
  date: string
  tss: number
  ctl: number | null
  atl: number | null
  tsb: number | null
  tsbPositive: number
  tsbNegative: number
  ctlProjected?: number
  atlProjected?: number
  tsbProjected?: number
  plannedTss?: number
  isProjected?: boolean
}

interface CustomTooltipProps {
  active?: boolean
  payload?: Array<{ payload: ChartDataPoint }>
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || !payload[0]) return null

  const data = payload[0].payload
  const isProjected = data.isProjected
  const tsb = isProjected ? data.tsbProjected : data.tsb
  const form = getFormStatus(tsb ?? null)

  return (
    <div className="bg-background border rounded-lg shadow-lg p-3 text-sm">
      <p className="font-semibold mb-2">
        {format(parseISO(data.date), 'EEEE, MMMM d, yyyy')}
        {isProjected && <span className="text-muted-foreground ml-2">(Projected)</span>}
      </p>
      <div className="space-y-1">
        {isProjected ? (
          <>
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Planned TSS:</span>
              <span className="font-medium">{data.plannedTss?.toFixed(0) || 0}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-blue-400">Projected CTL:</span>
              <span className="font-medium">{data.ctlProjected?.toFixed(1) || 0}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-red-400">Projected ATL:</span>
              <span className="font-medium">{data.atlProjected?.toFixed(1) || 0}</span>
            </div>
            <div className="flex justify-between gap-4 pt-1 border-t">
              <span style={{ color: form.color }}>Projected TSB:</span>
              <span className="font-medium" style={{ color: form.color }}>
                {data.tsbProjected?.toFixed(1) || 0} ({form.label})
              </span>
            </div>
          </>
        ) : (
          <>
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Daily TSS:</span>
              <span className="font-medium">{data.tss?.toFixed(0) || 0}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-blue-600">Fitness (CTL):</span>
              <span className="font-medium">{data.ctl?.toFixed(1) || 0}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-red-500">Fatigue (ATL):</span>
              <span className="font-medium">{data.atl?.toFixed(1) || 0}</span>
            </div>
            <div className="flex justify-between gap-4 pt-1 border-t">
              <span style={{ color: form.color }}>Form (TSB):</span>
              <span className="font-medium" style={{ color: form.color }}>
                {data.tsb?.toFixed(1) || 0} ({form.label})
              </span>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export function PMCChart({ data, projectedData, showProjection, onToggleProjection, projectionLoading }: PMCChartProps) {
  // Build historical chart data
  const historicalData: ChartDataPoint[] = data.map((item) => ({
    date: item.date,
    tss: item.total_tss,
    ctl: item.ctl,
    atl: item.atl,
    tsb: item.tsb,
    tsbPositive: item.tsb && item.tsb > 0 ? item.tsb : 0,
    tsbNegative: item.tsb && item.tsb < 0 ? item.tsb : 0,
    isProjected: false,
  }))

  // Build projected chart data
  const projectedChartData: ChartDataPoint[] = projectedData?.map((item) => ({
    date: item.date,
    tss: 0,
    ctl: null,
    atl: null,
    tsb: null,
    tsbPositive: 0,
    tsbNegative: 0,
    ctlProjected: item.ctlProjected,
    atlProjected: item.atlProjected,
    tsbProjected: item.tsbProjected,
    plannedTss: item.plannedTss,
    isProjected: true,
  })) || []

  // Merge historical and projected data
  const chartData = [...historicalData, ...projectedChartData]

  // Get today's date for the reference line
  const today = format(new Date(), 'yyyy-MM-dd')

  // Calculate TSB range for zone display (include projected values)
  const allTsbValues = [
    ...data.map(d => d.tsb).filter((v): v is number => v !== null),
    ...(projectedData?.map(d => d.tsbProjected) || []),
  ]
  const minTsb = Math.min(...allTsbValues, -35)
  const maxTsb = Math.max(...allTsbValues, 30)

  // Get current metrics for summary
  const latest = data[data.length - 1]
  const currentForm = latest ? getFormStatus(latest.tsb) : null

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Performance Management Chart</CardTitle>
            <CardDescription>
              Track your fitness, fatigue, and form over time
            </CardDescription>
          </div>
          <div className="flex items-center gap-6">
            {onToggleProjection && (
              <div className="flex items-center gap-2">
                <Switch
                  id="show-projection"
                  checked={showProjection}
                  onCheckedChange={onToggleProjection}
                  disabled={projectionLoading}
                />
                <Label htmlFor="show-projection" className="text-sm cursor-pointer">
                  {projectionLoading ? 'Loading...' : 'Show Projection'}
                </Label>
              </div>
            )}
            {latest && (
              <div className="text-right text-sm">
                <div className="flex items-center gap-4">
                  <div>
                    <span className="text-muted-foreground">CTL: </span>
                    <span className="font-semibold text-blue-600">{latest.ctl?.toFixed(0)}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">ATL: </span>
                    <span className="font-semibold text-red-500">{latest.atl?.toFixed(0)}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">TSB: </span>
                    <span className="font-semibold" style={{ color: currentForm?.color }}>
                      {latest.tsb?.toFixed(0)} ({currentForm?.label})
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[450px]">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 20, right: 60, left: 10, bottom: 20 }}>
              <defs>
                <linearGradient id="tsbPositiveGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#22c55e" stopOpacity={0.5} />
                  <stop offset="100%" stopColor="#22c55e" stopOpacity={0.05} />
                </linearGradient>
                <linearGradient id="tsbNegativeGradient" x1="0" y1="1" x2="0" y2="0">
                  <stop offset="0%" stopColor="#f97316" stopOpacity={0.5} />
                  <stop offset="100%" stopColor="#f97316" stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />

              {/* TSB Zone backgrounds on right axis - y1/y2 must stay within axis domain or ReferenceArea won't render (Recharts bug #1335) */}
              <ReferenceArea yAxisId="right" y1={25} y2={maxTsb + 5} fill={TSB_ZONES.OVER_FRESH.color} fillOpacity={0.3} />
              <ReferenceArea yAxisId="right" y1={5} y2={25} fill={TSB_ZONES.FRESH.color} fillOpacity={0.3} />
              <ReferenceArea yAxisId="right" y1={-10} y2={5} fill={TSB_ZONES.NEUTRAL.color} fillOpacity={0.3} />
              <ReferenceArea yAxisId="right" y1={-30} y2={-10} fill={TSB_ZONES.OPTIMAL.color} fillOpacity={0.3} />
              <ReferenceArea yAxisId="right" y1={minTsb - 5} y2={-30} fill={TSB_ZONES.HIGH_RISK.color} fillOpacity={0.3} />

              <XAxis
                dataKey="date"
                tickFormatter={(value) => format(parseISO(value), 'MMM d')}
                tick={{ fontSize: 11 }}
                stroke="#9ca3af"
                axisLine={{ stroke: '#d1d5db' }}
              />
              <YAxis
                yAxisId="left"
                orientation="left"
                tick={{ fontSize: 11 }}
                stroke="#9ca3af"
                axisLine={{ stroke: '#d1d5db' }}
                label={{
                  value: 'Training Load (TSS)',
                  angle: -90,
                  position: 'insideLeft',
                  style: { fontSize: 12, fill: '#6b7280' },
                  offset: 0,
                }}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                tick={{ fontSize: 11 }}
                stroke="#9ca3af"
                axisLine={{ stroke: '#d1d5db' }}
                domain={[minTsb - 5, maxTsb + 5]}
                label={{
                  value: 'Form (TSB)',
                  angle: 90,
                  position: 'insideRight',
                  style: { fontSize: 12, fill: '#6b7280' },
                  offset: 0,
                }}
              />

              <Tooltip content={<CustomTooltip />} />

              <Legend
                verticalAlign="top"
                height={36}
                formatter={(value) => {
                  const labels: Record<string, string> = {
                    tss: 'Daily TSS',
                    plannedTss: 'Planned TSS',
                    ctl: 'Fitness (CTL)',
                    atl: 'Fatigue (ATL)',
                    tsb: 'Form (TSB)',
                    ctlProjected: 'Projected CTL',
                    atlProjected: 'Projected ATL',
                    tsbProjected: 'Projected TSB',
                  }
                  return <span className="text-sm">{labels[value] || value}</span>
                }}
              />

              {/* TSB reference lines */}
              <ReferenceLine yAxisId="right" y={0} stroke="#6b7280" strokeWidth={1} />
              <ReferenceLine yAxisId="right" y={5} stroke="#22c55e" strokeDasharray="3 3" strokeOpacity={0.5} />
              <ReferenceLine yAxisId="right" y={-10} stroke="#f59e0b" strokeDasharray="3 3" strokeOpacity={0.5} />
              <ReferenceLine yAxisId="right" y={-30} stroke="#ef4444" strokeDasharray="3 3" strokeOpacity={0.5} />

              {/* TSB filled areas */}
              <Area
                yAxisId="right"
                type="monotone"
                dataKey="tsbPositive"
                fill="url(#tsbPositiveGradient)"
                stroke="none"
                legendType="none"
              />
              <Area
                yAxisId="right"
                type="monotone"
                dataKey="tsbNegative"
                fill="url(#tsbNegativeGradient)"
                stroke="none"
                legendType="none"
                baseValue={0}
              />

              {/* TSS bars - actual */}
              <Bar yAxisId="left" dataKey="tss" fill="#cbd5e1" name="tss" barSize={8} radius={[2, 2, 0, 0]} />

              {/* TSS bars - planned (outline style) */}
              {showProjection && (
                <Bar
                  yAxisId="left"
                  dataKey="plannedTss"
                  fill="#e2e8f0"
                  stroke="#94a3b8"
                  strokeWidth={1}
                  strokeDasharray="3 2"
                  name="plannedTss"
                  barSize={8}
                  radius={[2, 2, 0, 0]}
                />
              )}

              {/* Training load lines */}
              <Line yAxisId="left" type="monotone" dataKey="ctl" stroke="#3b82f6" strokeWidth={2.5} dot={false} name="ctl" />
              <Line yAxisId="left" type="monotone" dataKey="atl" stroke="#ef4444" strokeWidth={2} dot={false} name="atl" strokeDasharray="4 2" />

              {/* TSB line on top */}
              <Line yAxisId="right" type="monotone" dataKey="tsb" stroke="#16a34a" strokeWidth={2} dot={false} name="tsb" />

              {/* Today marker - vertical line separating historical from projected */}
              {showProjection && projectedData && projectedData.length > 0 && (
                <ReferenceLine
                  x={today}
                  yAxisId="left"
                  stroke="#6b7280"
                  strokeWidth={2}
                  strokeDasharray="4 4"
                  label={{ value: 'Today', position: 'top', fill: '#6b7280', fontSize: 11 }}
                />
              )}

              {/* Projected lines - dashed and lighter colors */}
              {showProjection && (
                <>
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="ctlProjected"
                    stroke="#93c5fd"
                    strokeWidth={2.5}
                    strokeDasharray="6 3"
                    dot={false}
                    name="ctlProjected"
                    connectNulls={false}
                  />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="atlProjected"
                    stroke="#fca5a5"
                    strokeWidth={2}
                    strokeDasharray="6 3"
                    dot={false}
                    name="atlProjected"
                    connectNulls={false}
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="tsbProjected"
                    stroke="#86efac"
                    strokeWidth={2}
                    strokeDasharray="6 3"
                    dot={false}
                    name="tsbProjected"
                    connectNulls={false}
                  />
                </>
              )}
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        {/* Zone legend */}
        <div className="flex flex-wrap justify-center gap-4 mt-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: TSB_ZONES.HIGH_RISK.color }} />
            <span>TSB &lt; -30: High Fatigue</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: TSB_ZONES.OPTIMAL.color }} />
            <span>-30 to -10: Optimal Training</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: TSB_ZONES.NEUTRAL.color }} />
            <span>-10 to +5: Grey Zone</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: TSB_ZONES.FRESH.color }} />
            <span>+5 to +25: Race Ready</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: TSB_ZONES.OVER_FRESH.color }} />
            <span>&gt; +25: Losing Fitness</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
