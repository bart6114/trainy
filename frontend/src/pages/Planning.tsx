import { format, parseISO, startOfWeek, addDays, isSameDay } from 'date-fns'
import { Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useUpcomingWorkouts, useDeleteWorkout, useSkipWorkout } from '@/hooks/usePlanning'
import { WorkoutPlanningChat } from '@/components/planning/WorkoutPlanningChat'
import { formatDuration, formatDistance } from '@/lib/utils'
import type { PlannedWorkout } from '@/types'

interface WeekData {
  weekStart: Date
  days: { date: Date; workouts: PlannedWorkout[] }[]
  totalDuration: number
  totalDistance: number
}

function groupWorkoutsByWeek(workouts: PlannedWorkout[]): WeekData[] {
  const weekMap = new Map<string, WeekData>()

  workouts.forEach(workout => {
    const date = parseISO(workout.planned_date)
    const weekStart = startOfWeek(date, { weekStartsOn: 1 }) // Monday
    const weekKey = format(weekStart, 'yyyy-MM-dd')

    if (!weekMap.has(weekKey)) {
      const days = Array.from({ length: 7 }, (_, i) => ({
        date: addDays(weekStart, i),
        workouts: [] as PlannedWorkout[]
      }))
      weekMap.set(weekKey, {
        weekStart,
        days,
        totalDuration: 0,
        totalDistance: 0
      })
    }

    const week = weekMap.get(weekKey)!
    const dayIndex = week.days.findIndex(d => isSameDay(d.date, date))
    if (dayIndex >= 0) {
      week.days[dayIndex].workouts.push(workout)
    }
    week.totalDuration += workout.target_duration_s || 0
    week.totalDistance += workout.target_distance_m || 0
  })

  return Array.from(weekMap.values()).sort(
    (a, b) => a.weekStart.getTime() - b.weekStart.getTime()
  )
}

const DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

function WorkoutCell({
  workout,
  onDelete,
  onSkip
}: {
  workout: PlannedWorkout
  onDelete: () => void
  onSkip: () => void
}) {
  return (
    <div className="p-1.5 mb-1 rounded border bg-card text-xs">
      <div className="flex items-center gap-1 mb-0.5">
        <Badge variant="outline" className="text-[10px] px-1 py-0">
          {workout.activity_type}
        </Badge>
        {workout.status === 'completed' && (
          <Badge className="bg-green-100 text-green-800 text-[10px] px-1 py-0">Done</Badge>
        )}
        {workout.status === 'skipped' && (
          <Badge variant="secondary" className="text-[10px] px-1 py-0">Skipped</Badge>
        )}
      </div>
      <p className="font-medium truncate" title={workout.title}>{workout.title}</p>
      <div className="flex gap-2 text-muted-foreground">
        {workout.target_duration_s && (
          <span>{formatDuration(workout.target_duration_s)}</span>
        )}
        {workout.target_distance_m && (
          <span>{formatDistance(workout.target_distance_m)}</span>
        )}
      </div>
      {workout.status === 'planned' && (
        <div className="flex gap-1 mt-1">
          <Button variant="ghost" size="sm" className="h-5 px-1 text-[10px]" onClick={onSkip}>
            Skip
          </Button>
          <Button variant="ghost" size="icon" className="h-5 w-5" onClick={onDelete}>
            <Trash2 className="h-3 w-3" />
          </Button>
        </div>
      )}
    </div>
  )
}

function WeekRow({
  week,
  onDelete,
  onSkip
}: {
  week: WeekData
  onDelete: (id: number) => void
  onSkip: (id: number) => void
}) {
  return (
    <div className="grid grid-cols-8 border-b last:border-b-0">
      {week.days.map((day, i) => (
        <div
          key={i}
          className="border-r p-2 min-h-[100px]"
        >
          <div className="text-xs text-muted-foreground mb-1">
            {format(day.date, 'd MMM')}
          </div>
          {day.workouts.map(workout => (
            <WorkoutCell
              key={workout.id}
              workout={workout}
              onDelete={() => onDelete(workout.id)}
              onSkip={() => onSkip(workout.id)}
            />
          ))}
        </div>
      ))}
      {/* Summary column */}
      <div className="p-2 bg-muted/50">
        <div className="text-xs font-medium mb-2">Week Total</div>
        <div className="space-y-1 text-sm">
          <div>
            <span className="text-muted-foreground">Time:</span>{' '}
            <span className="font-medium">{formatDuration(week.totalDuration)}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Dist:</span>{' '}
            <span className="font-medium">{formatDistance(week.totalDistance)}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

function CalendarView({
  workouts,
  onDelete,
  onSkip
}: {
  workouts: PlannedWorkout[]
  onDelete: (id: number) => void
  onSkip: (id: number) => void
}) {
  const weeks = groupWorkoutsByWeek(workouts)

  if (weeks.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-muted-foreground text-center">
            No planned workouts yet. Generate some workouts using the form above!
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="border rounded-lg overflow-hidden">
      {/* Header row */}
      <div className="grid grid-cols-8 bg-muted border-b">
        {DAY_NAMES.map(day => (
          <div key={day} className="p-2 text-sm font-medium text-center border-r">
            {day}
          </div>
        ))}
        <div className="p-2 text-sm font-medium text-center">Summary</div>
      </div>
      {/* Week rows */}
      {weeks.map(week => (
        <WeekRow
          key={format(week.weekStart, 'yyyy-MM-dd')}
          week={week}
          onDelete={onDelete}
          onSkip={onSkip}
        />
      ))}
    </div>
  )
}

export function Planning() {
  const { data: upcomingWorkouts, isLoading: workoutsLoading } = useUpcomingWorkouts(30)
  const deleteWorkout = useDeleteWorkout()
  const skipWorkout = useSkipWorkout()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Workout Planning</h1>
        <p className="text-muted-foreground">Generate and manage your AI-powered training workouts</p>
      </div>

      <WorkoutPlanningChat />

      <div>
        <h2 className="text-xl font-semibold mb-4">Planned Workouts</h2>
        {workoutsLoading ? (
          <p className="text-muted-foreground">Loading workouts...</p>
        ) : (
          <CalendarView
            workouts={upcomingWorkouts?.workouts ?? []}
            onDelete={(id) => deleteWorkout.mutate(id)}
            onSkip={(id) => skipWorkout.mutate(id)}
          />
        )}
      </div>
    </div>
  )
}
