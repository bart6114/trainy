import { format } from 'date-fns'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { formatDuration, formatDistance } from '@/lib/utils'
import type { Activity } from '@/types'

interface ActivityCardProps {
  activity: Activity
  onClick?: () => void
}

export function ActivityCard({ activity, onClick }: ActivityCardProps) {
  return (
    <Card className="cursor-pointer hover:bg-muted/50 transition-colors" onClick={onClick}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <Badge variant="outline">{activity.activity_type}</Badge>
          <span className="text-sm text-muted-foreground">
            {format(new Date(activity.start_time), 'MMM d, yyyy')}
          </span>
        </div>
        <CardTitle className="text-lg">{activity.title || 'Untitled'}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-muted-foreground">Duration</p>
            <p className="font-medium">{formatDuration(activity.duration_seconds)}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Distance</p>
            <p className="font-medium">{formatDistance(activity.distance_meters)}</p>
          </div>
          {activity.avg_hr && (
            <div>
              <p className="text-muted-foreground">Avg HR</p>
              <p className="font-medium">{activity.avg_hr} bpm</p>
            </div>
          )}
          {activity.avg_power && (
            <div>
              <p className="text-muted-foreground">Avg Power</p>
              <p className="font-medium">{Math.round(activity.avg_power)} W</p>
            </div>
          )}
          {activity.calories && (
            <div>
              <p className="text-muted-foreground">Calories</p>
              <p className="font-medium">{activity.calories} kcal</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
