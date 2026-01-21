import { useState } from 'react'
import { format, subDays } from 'date-fns'
import { useDailyMetrics, useWeeklyTSS } from '@/hooks/useMetrics'
import { PMCChart } from '@/components/charts/PMCChart'
import { WeeklyTSSChart } from '@/components/charts/WeeklyTSSChart'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

const DATE_RANGES = [
  { value: '30', label: 'Last 30 days', weeks: 5 },
  { value: '60', label: 'Last 60 days', weeks: 9 },
  { value: '90', label: 'Last 90 days', weeks: 13 },
  { value: '180', label: 'Last 6 months', weeks: 26 },
  { value: '365', label: 'Last year', weeks: 52 },
]

export function Progress() {
  const [dateRange, setDateRange] = useState('90')

  const selectedRange = DATE_RANGES.find((r) => r.value === dateRange) || DATE_RANGES[2]
  const endDate = format(new Date(), 'yyyy-MM-dd')
  const startDate = format(subDays(new Date(), parseInt(dateRange)), 'yyyy-MM-dd')

  const { data: dailyMetrics, isLoading: dailyLoading } = useDailyMetrics(startDate, endDate)
  const { data: weeklyTSS, isLoading: weeklyLoading } = useWeeklyTSS(selectedRange.weeks)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Progress</h1>
          <p className="text-muted-foreground">Track your training load over time</p>
        </div>
        <Select value={dateRange} onValueChange={setDateRange}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Date range" />
          </SelectTrigger>
          <SelectContent>
            {DATE_RANGES.map((range) => (
              <SelectItem key={range.value} value={range.value}>
                {range.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* PMC Chart */}
      {dailyLoading ? (
        <div className="h-[400px] flex items-center justify-center text-muted-foreground">
          Loading chart data...
        </div>
      ) : dailyMetrics && dailyMetrics.items.length > 0 ? (
        <PMCChart data={dailyMetrics.items} />
      ) : (
        <div className="h-[400px] flex items-center justify-center text-muted-foreground">
          No data available for the selected range
        </div>
      )}

      {/* Weekly TSS Chart */}
      <h2 className="text-xl font-semibold">Weekly Training Load</h2>

      {weeklyLoading ? (
        <div className="h-[300px] flex items-center justify-center text-muted-foreground">
          Loading weekly data...
        </div>
      ) : weeklyTSS && weeklyTSS.items.length > 0 ? (
        <WeeklyTSSChart data={weeklyTSS.items} />
      ) : (
        <div className="h-[300px] flex items-center justify-center text-muted-foreground">
          No weekly data available
        </div>
      )}
    </div>
  )
}
