import { format } from 'date-fns'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { formatDuration, formatDistance, formatPace, formatSpeed, isCyclingActivity } from '@/lib/utils'
import type { Activity } from '@/types'

interface ActivityTableProps {
  activities: Activity[]
  onSelect?: (activity: Activity) => void
}

function formatSpeedOrPace(activity: Activity): string {
  if (isCyclingActivity(activity.activity_type)) {
    return formatSpeed(activity.avg_speed_mps)
  }
  return formatPace(activity.avg_speed_mps)
}

function formatPower(activity: Activity): { value: string; isNormalized: boolean } {
  if (activity.normalized_power) {
    return { value: `${Math.round(activity.normalized_power)} W`, isNormalized: true }
  }
  if (activity.avg_power) {
    return { value: `${Math.round(activity.avg_power)} W`, isNormalized: false }
  }
  return { value: '-', isNormalized: false }
}

export function ActivityTable({ activities, onSelect }: ActivityTableProps) {
  const hasAnyPowerData = activities.some(a => a.normalized_power || a.avg_power)

  return (
    <div className="space-y-2">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Date</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Title</TableHead>
            <TableHead>Duration</TableHead>
            <TableHead>Distance</TableHead>
            <TableHead>Speed/Pace</TableHead>
            <TableHead>HR</TableHead>
            {hasAnyPowerData && <TableHead>Power</TableHead>}
          </TableRow>
        </TableHeader>
        <TableBody>
          {activities.map((activity) => {
            const power = formatPower(activity)
            return (
              <TableRow
                key={activity.id}
                className="cursor-pointer"
                onClick={() => onSelect?.(activity)}
              >
                <TableCell className="font-medium">
                  {format(new Date(activity.start_time), 'MMM d, yyyy')}
                </TableCell>
                <TableCell>
                  <Badge variant="outline">{activity.activity_type}</Badge>
                </TableCell>
                <TableCell>{activity.title || 'Untitled'}</TableCell>
                <TableCell>{formatDuration(activity.duration_seconds)}</TableCell>
                <TableCell>{formatDistance(activity.distance_meters)}</TableCell>
                <TableCell>{formatSpeedOrPace(activity)}</TableCell>
                <TableCell>
                  {activity.avg_hr ? `${activity.avg_hr} bpm` : '-'}
                </TableCell>
                {hasAnyPowerData && (
                  <TableCell>
                    {power.isNormalized ? (
                      <span className="inline-flex items-center gap-1">
                        <span className="inline-flex items-center justify-center w-4 h-4 text-[10px] font-semibold bg-amber-100 text-amber-700 rounded">
                          NP
                        </span>
                        {power.value}
                      </span>
                    ) : (
                      power.value
                    )}
                  </TableCell>
                )}
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
      {hasAnyPowerData && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground px-2">
          <span className="inline-flex items-center justify-center w-4 h-4 text-[10px] font-semibold bg-amber-100 text-amber-700 rounded">
            NP
          </span>
          <span>= Normalized Power (weighted average that accounts for variability)</span>
        </div>
      )}
    </div>
  )
}
