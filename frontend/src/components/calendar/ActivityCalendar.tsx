import { useState, Fragment } from 'react'
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isToday, addMonths, subMonths, startOfWeek, endOfWeek } from 'date-fns'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useCalendarMonth } from '@/hooks/useCalendar'
import type { CalendarDay } from '@/types'
import { cn, formatDuration, formatDistance, getDayMaxIntensity, intensityBarColors } from '@/lib/utils'

interface ActivityCalendarProps {
  onDateSelect?: (date: Date) => void
}

const activityColors: Record<string, string> = {
  run: 'bg-blue-500',
  cycle: 'bg-green-500',
  swim: 'bg-cyan-500',
  strength: 'bg-orange-500',
  default: 'bg-gray-500',
}

const plannedColors: Record<string, string> = {
  run: 'border-blue-500',
  cycle: 'border-green-500',
  swim: 'border-cyan-500',
  strength: 'border-orange-500',
  default: 'border-gray-500',
}

export function ActivityCalendar({ onDateSelect }: ActivityCalendarProps) {
  const [currentMonth, setCurrentMonth] = useState(new Date())
  const year = currentMonth.getFullYear()
  const month = currentMonth.getMonth() + 1

  // Get all weeks that overlap with this month (starting Monday)
  const monthStart = startOfMonth(currentMonth)
  const monthEnd = endOfMonth(currentMonth)
  const calendarStart = startOfWeek(monthStart, { weekStartsOn: 1 })
  const calendarEnd = endOfWeek(monthEnd, { weekStartsOn: 1 })

  // Determine if we need adjacent months' data
  const prevMonth = subMonths(currentMonth, 1)
  const nextMonth = addMonths(currentMonth, 1)
  const needsPrevMonth = calendarStart.getMonth() !== currentMonth.getMonth()
  const needsNextMonth = calendarEnd.getMonth() !== currentMonth.getMonth()

  // Fetch current and adjacent months as needed
  const { data, isLoading } = useCalendarMonth(year, month)
  const { data: prevData } = useCalendarMonth(
    prevMonth.getFullYear(),
    prevMonth.getMonth() + 1
  )
  const { data: nextData } = useCalendarMonth(
    nextMonth.getFullYear(),
    nextMonth.getMonth() + 1
  )

  const allDays = eachDayOfInterval({ start: calendarStart, end: calendarEnd })

  // Group days into weeks
  const weeks: Date[][] = []
  for (let i = 0; i < allDays.length; i += 7) {
    weeks.push(allDays.slice(i, i + 7))
  }

  const getDayData = (date: Date): CalendarDay | undefined => {
    const dateStr = format(date, 'yyyy-MM-dd')
    const dateMonth = date.getMonth()

    // Check which month's data to use
    if (dateMonth === currentMonth.getMonth()) {
      return data?.days.find((d) => d.date === dateStr)
    } else if (needsPrevMonth && dateMonth === prevMonth.getMonth()) {
      return prevData?.days.find((d) => d.date === dateStr)
    } else if (needsNextMonth && dateMonth === nextMonth.getMonth()) {
      return nextData?.days.find((d) => d.date === dateStr)
    }
    return undefined
  }

  // Calculate week totals
  const getWeekTotals = (weekDays: Date[]) => {
    let totalDistance = 0
    let totalDuration = 0
    let totalTss = 0

    for (const day of weekDays) {
      const dayData = getDayData(day)
      if (dayData) {
        totalTss += dayData.total_tss
        for (const activity of dayData.activities) {
          totalDuration += activity.duration_seconds
          totalDistance += activity.distance_meters || 0
        }
      }
    }

    return { totalDistance, totalDuration, totalTss }
  }

  const getActivityDots = (dayData?: CalendarDay) => {
    if (!dayData) return null

    const plannedWorkouts = dayData.planned_workouts || []

    // Build set of activity IDs that completed planned workouts
    const completedPlannedActivityIds = new Set(
      plannedWorkouts
        .filter(w => w.status === 'completed' && w.completed_activity_id)
        .map(w => w.completed_activity_id)
    )

    // Get activities with their types and whether they were planned
    const activities = dayData.activities.map(a => ({
      id: a.id,
      type: a.activity_type,
      wasPlanned: completedPlannedActivityIds.has(a.id)
    }))

    // Get pending planned workouts (not yet completed)
    const pendingPlannedTypes = [...new Set(
      plannedWorkouts.filter(w => w.status === 'planned').map(w => w.activity_type)
    )]

    if (activities.length === 0 && pendingPlannedTypes.length === 0) return null

    return (
      <div className="flex justify-center gap-0.5 mt-1">
        {activities.slice(0, 2).map((activity, i) => (
          <div
            key={`act-${i}`}
            className={cn(
              'w-1.5 h-1.5',
              activity.wasPlanned ? 'rounded-none' : 'rounded-full',
              activityColors[activity.type] || activityColors.default
            )}
          />
        ))}
        {pendingPlannedTypes.slice(0, 2).map((type, i) => (
          <div
            key={`plan-${i}`}
            className={cn('w-1.5 h-1.5 rounded-none border bg-transparent', plannedColors[type] || plannedColors.default)}
          />
        ))}
      </div>
    )
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-lg font-medium">
          {format(currentMonth, 'MMMM yyyy')}
        </CardTitle>
        <div className="flex items-center space-x-1">
          <Button variant="ghost" size="icon" onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setCurrentMonth(new Date())}>
            Today
          </Button>
          <Button variant="ghost" size="icon" onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}>
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-8 gap-1 text-center">
          {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => (
            <div key={day} className="text-xs font-medium text-muted-foreground py-2">
              {day}
            </div>
          ))}
          <div className="text-xs font-medium text-muted-foreground py-2">
            Week
          </div>
          {weeks.map((week, weekIndex) => {
            const weekTotals = getWeekTotals(week)
            const hasWeekData = weekTotals.totalDistance > 0 || weekTotals.totalDuration > 0 || weekTotals.totalTss > 0

            return (
              <Fragment key={`week-row-${weekIndex}`}>
                {week.map((date) => {
                  const dayData = getDayData(date)
                  const hasActivities = dayData && dayData.activities.length > 0
                  const dayIntensity = dayData
                    ? getDayMaxIntensity(dayData.planned_workouts, dayData.activities)
                    : null

                  return (
                    <button
                      key={date.toISOString()}
                      onClick={() => onDateSelect?.(date)}
                      className={cn(
                        'relative p-2 rounded-md transition-colors hover:bg-accent',
                        !isSameMonth(date, currentMonth) && 'text-muted-foreground opacity-50',
                        isToday(date) && 'bg-primary text-primary-foreground hover:bg-primary/90',
                        hasActivities && !isToday(date) && 'bg-muted'
                      )}
                    >
                      <div className="text-sm">{format(date, 'd')}</div>
                      {getActivityDots(dayData)}
                      {dayIntensity && (
                        <div
                          className={cn(
                            'absolute bottom-0.5 left-1 right-1 h-0.5 rounded-full',
                            intensityBarColors[dayIntensity]
                          )}
                        />
                      )}
                    </button>
                  )
                })}
                <div
                  key={`week-${weekIndex}`}
                  className={cn(
                    'p-1 rounded-md text-left text-xs border-l border-border',
                    hasWeekData && 'bg-muted/50'
                  )}
                >
                  {hasWeekData ? (
                    <div className="space-y-0.5">
                      {weekTotals.totalDistance > 0 && (
                        <div className="text-muted-foreground truncate">
                          {formatDistance(weekTotals.totalDistance)}
                        </div>
                      )}
                      {weekTotals.totalDuration > 0 && (
                        <div className="text-muted-foreground truncate">
                          {formatDuration(weekTotals.totalDuration)}
                        </div>
                      )}
                      {weekTotals.totalTss > 0 && (
                        <div className="text-muted-foreground truncate">
                          {Math.round(weekTotals.totalTss)} TSS
                        </div>
                      )}
                    </div>
                  ) : null}
                </div>
              </Fragment>
            )
          })}
        </div>
        {isLoading && <div className="text-center text-sm text-muted-foreground mt-2">Loading...</div>}
      </CardContent>
    </Card>
  )
}
