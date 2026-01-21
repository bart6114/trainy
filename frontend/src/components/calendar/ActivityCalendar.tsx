import { useState } from 'react'
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isToday, addMonths, subMonths } from 'date-fns'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useCalendarMonth } from '@/hooks/useCalendar'
import type { CalendarDay } from '@/types'
import { cn } from '@/lib/utils'

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

  const { data, isLoading } = useCalendarMonth(year, month)

  const daysInMonth = eachDayOfInterval({
    start: startOfMonth(currentMonth),
    end: endOfMonth(currentMonth),
  })

  const getDayData = (date: Date): CalendarDay | undefined => {
    if (!data) return undefined
    const dateStr = format(date, 'yyyy-MM-dd')
    return data.days.find((d) => d.date === dateStr)
  }

  const getActivityDots = (dayData?: CalendarDay) => {
    if (!dayData) return null

    const activityTypes = [...new Set(dayData.activities.map((a) => a.activity_type))]
    const plannedWorkouts = dayData.planned_workouts || []
    const plannedTypes = [...new Set(
      plannedWorkouts.filter(w => w.status === 'planned').map((w) => w.activity_type)
    )]

    if (activityTypes.length === 0 && plannedTypes.length === 0) return null

    return (
      <div className="flex justify-center gap-0.5 mt-1">
        {activityTypes.slice(0, 2).map((type, i) => (
          <div
            key={`act-${i}`}
            className={cn('w-1.5 h-1.5 rounded-full', activityColors[type] || activityColors.default)}
          />
        ))}
        {plannedTypes.slice(0, 2).map((type, i) => (
          <div
            key={`plan-${i}`}
            className={cn('w-1.5 h-1.5 rounded-full border bg-transparent', plannedColors[type] || plannedColors.default)}
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
        <div className="grid grid-cols-7 gap-1 text-center">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
            <div key={day} className="text-xs font-medium text-muted-foreground py-2">
              {day}
            </div>
          ))}
          {Array.from({ length: startOfMonth(currentMonth).getDay() }).map((_, i) => (
            <div key={`empty-${i}`} />
          ))}
          {daysInMonth.map((date) => {
            const dayData = getDayData(date)
            const hasActivities = dayData && dayData.activities.length > 0

            return (
              <button
                key={date.toISOString()}
                onClick={() => onDateSelect?.(date)}
                className={cn(
                  'p-2 rounded-md transition-colors hover:bg-accent',
                  !isSameMonth(date, currentMonth) && 'text-muted-foreground',
                  isToday(date) && 'bg-primary text-primary-foreground hover:bg-primary/90',
                  hasActivities && !isToday(date) && 'bg-muted'
                )}
              >
                <div className="text-sm">{format(date, 'd')}</div>
                {getActivityDots(dayData)}
              </button>
            )
          })}
        </div>
        {isLoading && <div className="text-center text-sm text-muted-foreground mt-2">Loading...</div>}
      </CardContent>
    </Card>
  )
}
