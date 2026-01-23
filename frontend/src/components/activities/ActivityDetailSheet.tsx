import { format } from 'date-fns'
import { X } from 'lucide-react'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { Badge } from '@/components/ui/badge'
import { useActivity, useActivityTrack } from '@/hooks/useActivities'
import { formatDuration, formatPace, formatSpeed, isCyclingActivity } from '@/lib/utils'
import { ActivityRouteMap } from './ActivityRouteMap'

interface ActivityDetailSheetProps {
  activityId: number | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

interface MetricItemProps {
  label: string
  value: string | number | null | undefined
  unit?: string
}

function MetricItem({ label, value, unit }: MetricItemProps) {
  if (value === null || value === undefined || value === '-') return null
  return (
    <div className="flex flex-col">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-lg font-semibold">
        {value}
        {unit && <span className="text-sm font-normal text-muted-foreground ml-1">{unit}</span>}
      </span>
    </div>
  )
}

interface MetricSectionProps {
  title: string
  children: React.ReactNode
}

function MetricSection({ title, children }: MetricSectionProps) {
  return (
    <div className="space-y-2">
      <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{title}</h4>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        {children}
      </div>
    </div>
  )
}

export function ActivityDetailSheet({ activityId, open, onOpenChange }: ActivityDetailSheetProps) {
  const { data, isLoading } = useActivity(activityId ?? 0)
  const { data: trackData, isLoading: trackLoading } = useActivityTrack(activityId ?? 0, open && !!activityId)

  const activity = data?.activity
  const metrics = data?.metrics
  const isCycling = activity ? isCyclingActivity(activity.activity_type) : false
  const isRunning = activity?.activity_type === 'run'

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
        <SheetHeader className="space-y-1 pr-6">
          <div className="flex items-center gap-2">
            <SheetTitle className="text-xl">
              {isLoading ? 'Loading...' : activity?.title || 'Activity'}
            </SheetTitle>
            <button
              onClick={() => onOpenChange(false)}
              className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
            >
              <X className="h-4 w-4" />
              <span className="sr-only">Close</span>
            </button>
          </div>
          {activity && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span>{format(new Date(activity.start_time), 'EEEE, MMMM d, yyyy')}</span>
              <span>-</span>
              <Badge variant="outline">{activity.activity_type}</Badge>
            </div>
          )}
        </SheetHeader>

        {isLoading ? (
          <div className="flex items-center justify-center h-48">
            <p className="text-muted-foreground">Loading activity details...</p>
          </div>
        ) : activity ? (
          <div className="mt-6 space-y-6">
            {/* Map */}
            {!trackLoading && trackData?.has_track && (
              <div className="h-48 rounded-lg overflow-hidden">
                <ActivityRouteMap points={trackData.points} className="h-full" />
              </div>
            )}

            {/* Overview */}
            <MetricSection title="Overview">
              <MetricItem label="Duration" value={formatDuration(activity.duration_seconds)} />
              <MetricItem label="Distance" value={activity.distance_km} unit="km" />
              <MetricItem label="Calories" value={activity.calories} unit="kcal" />
            </MetricSection>

            {/* Heart Rate */}
            {(activity.avg_hr || activity.max_hr) && (
              <MetricSection title="Heart Rate">
                <MetricItem label="Average" value={activity.avg_hr} unit="bpm" />
                <MetricItem label="Max" value={activity.max_hr} unit="bpm" />
              </MetricSection>
            )}

            {/* Power (cycling) */}
            {isCycling && (activity.avg_power || activity.normalized_power || activity.max_power) && (
              <MetricSection title="Power">
                <MetricItem label="Average" value={activity.avg_power ? Math.round(activity.avg_power) : null} unit="W" />
                <MetricItem label="Normalized" value={activity.normalized_power ? Math.round(activity.normalized_power) : null} unit="W" />
                <MetricItem label="Max" value={activity.max_power ? Math.round(activity.max_power) : null} unit="W" />
              </MetricSection>
            )}

            {/* Pace/Speed */}
            {(activity.avg_speed_mps || activity.max_speed_mps) && (
              <MetricSection title={isRunning ? 'Pace' : 'Speed'}>
                {isRunning ? (
                  <>
                    <MetricItem label="Average" value={formatPace(activity.avg_speed_mps)} />
                    <MetricItem label="Max" value={formatPace(activity.max_speed_mps)} />
                  </>
                ) : (
                  <>
                    <MetricItem label="Average" value={formatSpeed(activity.avg_speed_mps)} />
                    <MetricItem label="Max" value={formatSpeed(activity.max_speed_mps)} />
                  </>
                )}
              </MetricSection>
            )}

            {/* Elevation */}
            {(activity.total_ascent_m || activity.total_descent_m) && (
              <MetricSection title="Elevation">
                <MetricItem label="Ascent" value={activity.total_ascent_m ? Math.round(activity.total_ascent_m) : null} unit="m" />
                <MetricItem label="Descent" value={activity.total_descent_m ? Math.round(activity.total_descent_m) : null} unit="m" />
              </MetricSection>
            )}

            {/* Training Metrics */}
            {(metrics?.tss || metrics?.intensity_factor || activity.avg_cadence) && (
              <MetricSection title="Training Metrics">
                <MetricItem label="TSS" value={metrics?.tss ? Math.round(metrics.tss) : null} />
                <MetricItem label="IF" value={metrics?.intensity_factor?.toFixed(2)} />
                <MetricItem label="Cadence" value={activity.avg_cadence} unit={isRunning ? 'spm' : 'rpm'} />
              </MetricSection>
            )}

            {/* Peak Powers (cycling) */}
            {isCycling && (metrics?.peak_power_5s || metrics?.peak_power_1min || metrics?.peak_power_5min || metrics?.peak_power_20min) && (
              <MetricSection title="Peak Powers">
                <MetricItem label="5 sec" value={metrics?.peak_power_5s ? Math.round(metrics.peak_power_5s) : null} unit="W" />
                <MetricItem label="1 min" value={metrics?.peak_power_1min ? Math.round(metrics.peak_power_1min) : null} unit="W" />
                <MetricItem label="5 min" value={metrics?.peak_power_5min ? Math.round(metrics.peak_power_5min) : null} unit="W" />
                <MetricItem label="20 min" value={metrics?.peak_power_20min ? Math.round(metrics.peak_power_20min) : null} unit="W" />
              </MetricSection>
            )}

            {/* Efficiency (cycling) */}
            {isCycling && (metrics?.efficiency_factor || metrics?.variability_index) && (
              <MetricSection title="Efficiency">
                <MetricItem label="EF" value={metrics?.efficiency_factor?.toFixed(2)} />
                <MetricItem label="VI" value={metrics?.variability_index?.toFixed(2)} />
              </MetricSection>
            )}
          </div>
        ) : (
          <div className="flex items-center justify-center h-48">
            <p className="text-muted-foreground">Activity not found</p>
          </div>
        )}
      </SheetContent>
    </Sheet>
  )
}
