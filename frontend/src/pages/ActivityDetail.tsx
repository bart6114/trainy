import { useState, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { format } from 'date-fns'
import { ArrowLeft, Clock, MapPin, Flame, Heart, Zap, TrendingUp } from 'lucide-react'
import { useActivity, useActivityStreams } from '@/hooks/useActivities'
import { ActivityStreamsChart } from '@/components/activities/ActivityStreamsChart'
import { ActivityRouteMapWithMarker } from '@/components/activities/ActivityRouteMapWithMarker'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatDuration, formatPace, formatSpeed, isCyclingActivity } from '@/lib/utils'

interface StatItemProps {
  icon: React.ReactNode
  label: string
  value: string | number | null | undefined
  unit?: string
}

function StatItem({ icon, label, value, unit }: StatItemProps) {
  if (value === null || value === undefined) return null
  return (
    <div className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg">
      <div className="text-muted-foreground">{icon}</div>
      <div>
        <div className="text-xs text-muted-foreground">{label}</div>
        <div className="text-lg font-semibold">
          {value}
          {unit && <span className="text-sm font-normal text-muted-foreground ml-1">{unit}</span>}
        </div>
      </div>
    </div>
  )
}

export function ActivityDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const activityId = id ? parseInt(id, 10) : 0

  const { data: activityData, isLoading: activityLoading } = useActivity(activityId)
  const { data: streamsData, isLoading: streamsLoading } = useActivityStreams(activityId)

  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null)

  const activity = activityData?.activity
  const metrics = activityData?.metrics
  const isCycling = activity ? isCyclingActivity(activity.activity_type) : false
  const isRunning = activity?.activity_type === 'run'

  const hoveredPosition = useMemo(() => {
    if (hoveredIndex === null || !streamsData?.position) return null
    const pos = streamsData.position[hoveredIndex]
    return pos || null
  }, [hoveredIndex, streamsData?.position])

  if (activityLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-muted-foreground">Loading activity...</div>
      </div>
    )
  }

  if (!activity) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <div className="text-muted-foreground">Activity not found</div>
        <Button variant="outline" onClick={() => navigate('/activities')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Activities
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <Button
            variant="ghost"
            size="sm"
            className="mb-2 -ml-2"
            onClick={() => navigate('/activities')}
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Activities
          </Button>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold tracking-tight">{activity.title}</h1>
            <Badge variant="outline" className="capitalize">
              {activity.activity_type}
            </Badge>
          </div>
          <p className="text-muted-foreground">
            {format(new Date(activity.start_time), 'EEEE, MMMM d, yyyy · h:mm a')}
          </p>
        </div>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <StatItem
          icon={<Clock className="h-5 w-5" />}
          label="Duration"
          value={formatDuration(activity.duration_seconds)}
        />
        <StatItem
          icon={<MapPin className="h-5 w-5" />}
          label="Distance"
          value={activity.distance_km}
          unit="km"
        />
        <StatItem
          icon={<Heart className="h-5 w-5" />}
          label="Avg HR"
          value={activity.avg_hr}
          unit="bpm"
        />
        {isCycling && (
          <StatItem
            icon={<Zap className="h-5 w-5" />}
            label="Avg Power"
            value={activity.avg_power ? Math.round(activity.avg_power) : null}
            unit="W"
          />
        )}
        <StatItem
          icon={<TrendingUp className="h-5 w-5" />}
          label="Elevation"
          value={activity.total_ascent_m ? Math.round(activity.total_ascent_m) : null}
          unit="m"
        />
        <StatItem
          icon={<Flame className="h-5 w-5" />}
          label="Calories"
          value={activity.calories}
          unit="kcal"
        />
      </div>

      {/* Main content: Map and Charts */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Map */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">Route</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[400px] rounded-lg overflow-hidden">
              <ActivityRouteMapWithMarker
                activityId={activityId}
                markerPosition={hoveredPosition}
                className="h-full"
              />
            </div>
          </CardContent>
        </Card>

        {/* Charts */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">Activity Data</CardTitle>
          </CardHeader>
          <CardContent>
            {streamsLoading ? (
              <div className="flex items-center justify-center h-[400px]">
                <div className="text-muted-foreground">Loading streams...</div>
              </div>
            ) : streamsData && streamsData.timestamps.length > 0 ? (
              <ActivityStreamsChart
                streams={streamsData}
                activityType={activity.activity_type}
                hoveredIndex={hoveredIndex}
                onHoverIndexChange={setHoveredIndex}
              />
            ) : (
              <div className="flex items-center justify-center h-[400px] text-muted-foreground">
                No time series data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Additional metrics */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Pace/Speed */}
        {(activity.avg_speed_mps || activity.max_speed_mps) && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">{isRunning ? 'Pace' : 'Speed'}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                {isRunning ? (
                  <>
                    <div>
                      <div className="text-sm text-muted-foreground">Average</div>
                      <div className="text-xl font-semibold">{formatPace(activity.avg_speed_mps)}</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Best</div>
                      <div className="text-xl font-semibold">{formatPace(activity.max_speed_mps)}</div>
                    </div>
                  </>
                ) : (
                  <>
                    <div>
                      <div className="text-sm text-muted-foreground">Average</div>
                      <div className="text-xl font-semibold">{formatSpeed(activity.avg_speed_mps)}</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Max</div>
                      <div className="text-xl font-semibold">{formatSpeed(activity.max_speed_mps)}</div>
                    </div>
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Heart Rate */}
        {(activity.avg_hr || activity.max_hr) && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Heart Rate</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-muted-foreground">Average</div>
                  <div className="text-xl font-semibold">{activity.avg_hr} <span className="text-sm font-normal text-muted-foreground">bpm</span></div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Max</div>
                  <div className="text-xl font-semibold">{activity.max_hr} <span className="text-sm font-normal text-muted-foreground">bpm</span></div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Power (cycling) */}
        {isCycling && (activity.avg_power || activity.normalized_power) && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Power</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <div className="text-sm text-muted-foreground">Average</div>
                  <div className="text-xl font-semibold">{activity.avg_power ? Math.round(activity.avg_power) : '-'} <span className="text-sm font-normal text-muted-foreground">W</span></div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Normalized</div>
                  <div className="text-xl font-semibold">{activity.normalized_power ? Math.round(activity.normalized_power) : '-'} <span className="text-sm font-normal text-muted-foreground">W</span></div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Max</div>
                  <div className="text-xl font-semibold">{activity.max_power ? Math.round(activity.max_power) : '-'} <span className="text-sm font-normal text-muted-foreground">W</span></div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Training Metrics */}
        {(metrics?.tss || metrics?.intensity_factor) && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Training Load</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <div className="text-sm text-muted-foreground">TSS</div>
                  <div className="text-xl font-semibold">{metrics?.tss ? Math.round(metrics.tss) : '-'}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">IF</div>
                  <div className="text-xl font-semibold">{metrics?.intensity_factor?.toFixed(2) ?? '-'}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Cadence</div>
                  <div className="text-xl font-semibold">{activity.avg_cadence ?? '-'} <span className="text-sm font-normal text-muted-foreground">{isRunning ? 'spm' : 'rpm'}</span></div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Peak Powers (cycling) */}
        {isCycling && (metrics?.peak_power_5s || metrics?.peak_power_1min || metrics?.peak_power_5min) && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Peak Powers</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-4 gap-4">
                <div>
                  <div className="text-sm text-muted-foreground">5s</div>
                  <div className="text-xl font-semibold">{metrics?.peak_power_5s ? Math.round(metrics.peak_power_5s) : '-'} <span className="text-sm font-normal text-muted-foreground">W</span></div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">1m</div>
                  <div className="text-xl font-semibold">{metrics?.peak_power_1min ? Math.round(metrics.peak_power_1min) : '-'} <span className="text-sm font-normal text-muted-foreground">W</span></div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">5m</div>
                  <div className="text-xl font-semibold">{metrics?.peak_power_5min ? Math.round(metrics.peak_power_5min) : '-'} <span className="text-sm font-normal text-muted-foreground">W</span></div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">20m</div>
                  <div className="text-xl font-semibold">{metrics?.peak_power_20min ? Math.round(metrics.peak_power_20min) : '-'} <span className="text-sm font-normal text-muted-foreground">W</span></div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Efficiency (cycling) */}
        {isCycling && (metrics?.efficiency_factor || metrics?.variability_index) && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Efficiency</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-muted-foreground">Efficiency Factor</div>
                  <div className="text-xl font-semibold">{metrics?.efficiency_factor?.toFixed(2) ?? '-'}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Variability Index</div>
                  <div className="text-xl font-semibold">{metrics?.variability_index?.toFixed(2) ?? '-'}</div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
