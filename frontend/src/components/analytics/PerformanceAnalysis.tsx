import { format, subDays } from 'date-fns'
import { useDailyMetrics } from '@/hooks/useMetrics'
import { PMCChart } from '@/components/charts/PMCChart'

interface PerformanceAnalysisProps {
  days: number
}

export function PerformanceAnalysis({ days }: PerformanceAnalysisProps) {
  const endDate = format(new Date(), 'yyyy-MM-dd')
  const startDate = format(subDays(new Date(), days), 'yyyy-MM-dd')

  const { data: dailyMetrics, isLoading } = useDailyMetrics(startDate, endDate)

  if (isLoading) {
    return (
      <div className="h-[400px] flex items-center justify-center text-muted-foreground">
        Loading chart data...
      </div>
    )
  }

  if (!dailyMetrics || dailyMetrics.items.length === 0) {
    return (
      <div className="h-[400px] flex items-center justify-center text-muted-foreground">
        No data available for the selected range
      </div>
    )
  }

  return <PMCChart data={dailyMetrics.items} />
}
