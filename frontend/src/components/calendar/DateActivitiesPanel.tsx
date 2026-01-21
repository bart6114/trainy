import { format } from 'date-fns'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useCalendarDate } from '@/hooks/useCalendar'
import { formatDuration, formatDistance } from '@/lib/utils'
import { ActivityFeedbackDisplay } from '@/components/wellness/ActivityFeedbackDisplay'

interface DateActivitiesPanelProps {
  date: Date | null
}

export function DateActivitiesPanel({ date }: DateActivitiesPanelProps) {
  const dateStr = date ? format(date, 'yyyy-MM-dd') : ''
  const { data, isLoading } = useCalendarDate(dateStr)

  if (!date) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Activities</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Select a date to view activities</p>
        </CardContent>
      </Card>
    )
  }

  const hasActivities = (data?.activities?.length ?? 0) > 0
  const plannedWorkouts = data?.planned_workouts ?? []
  const hasPlannedWorkouts = plannedWorkouts.length > 0
  const hasContent = hasActivities || hasPlannedWorkouts

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{format(date, 'EEEE, MMMM d, yyyy')}</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading...</p>
        ) : hasContent && data ? (
          <div className="space-y-4">
            {data.total_tss > 0 && (
              <p className="text-sm text-muted-foreground">
                Total TSS: <span className="font-medium text-foreground">{Math.round(data.total_tss)}</span>
              </p>
            )}

            {/* Planned Workouts */}
            {hasPlannedWorkouts && (
              <div>
                <h4 className="text-sm font-medium mb-2 text-muted-foreground">Planned</h4>
                {plannedWorkouts.map((workout) => (
                  <div key={workout.id} className="flex items-center justify-between py-2 border-b last:border-0">
                    <div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="border-dashed">{workout.activity_type}</Badge>
                        {workout.workout_type && (
                          <Badge variant="secondary" className="text-xs">{workout.workout_type}</Badge>
                        )}
                        <span className="font-medium">{workout.title}</span>
                      </div>
                      <div className="text-sm text-muted-foreground mt-1">
                        {workout.target_duration_s && formatDuration(workout.target_duration_s)}
                        {workout.description && ` - ${workout.description.slice(0, 50)}...`}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {workout.target_tss && (
                        <span className="text-sm">{Math.round(workout.target_tss)} TSS</span>
                      )}
                      {workout.status === 'completed' && (
                        <Badge className="bg-green-100 text-green-800 text-xs">Done</Badge>
                      )}
                      {workout.status === 'skipped' && (
                        <Badge variant="secondary" className="text-xs">Skipped</Badge>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Actual Activities */}
            {hasActivities && (
              <div>
                <h4 className="text-sm font-medium mb-2 text-muted-foreground">Completed</h4>
                {data.activities.map((activity) => (
                  <div key={activity.id} className="py-2 border-b last:border-0">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">{activity.activity_type}</Badge>
                          <span className="font-medium">{activity.title || 'Untitled'}</span>
                        </div>
                        <div className="text-sm text-muted-foreground mt-1">
                          {formatDuration(activity.duration_seconds)}
                          {activity.distance_meters && ` - ${formatDistance(activity.distance_meters)}`}
                        </div>
                      </div>
                      {activity.tss && (
                        <div className="text-sm font-medium">{Math.round(activity.tss)} TSS</div>
                      )}
                    </div>
                    <ActivityFeedbackDisplay activityId={activity.id} />
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No activities or workouts on this date</p>
        )}
      </CardContent>
    </Card>
  )
}
