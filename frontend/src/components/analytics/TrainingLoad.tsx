import { useWeeklyTSS } from '@/hooks/useMetrics'
import { WeeklyTSSChart } from '@/components/charts/WeeklyTSSChart'

interface TrainingLoadProps {
  days: number
}

const DAYS_TO_WEEKS: Record<number, number> = {
  30: 5,
  90: 13,
  180: 26,
  365: 52,
}

export function TrainingLoad({ days }: TrainingLoadProps) {
  const weeks = DAYS_TO_WEEKS[days] || Math.ceil(days / 7)
  const { data: weeklyTSS, isLoading } = useWeeklyTSS(weeks)

  if (isLoading) {
    return (
      <div className="h-[300px] flex items-center justify-center text-muted-foreground">
        Loading weekly data...
      </div>
    )
  }

  if (!weeklyTSS || weeklyTSS.items.length === 0) {
    return (
      <div className="h-[300px] flex items-center justify-center text-muted-foreground">
        No weekly data available
      </div>
    )
  }

  return <WeeklyTSSChart data={weeklyTSS.items} />
}
