import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { format, parseISO } from 'date-fns'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { WeeklyTSSItem } from '@/types'

interface WeeklyTSSChartProps {
  data: WeeklyTSSItem[]
}

export function WeeklyTSSChart({ data }: WeeklyTSSChartProps) {
  const chartData = data.map((item) => ({
    week: format(parseISO(item.week_start), 'MMM d'),
    tss: item.total_tss,
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle>Weekly TSS</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis dataKey="week" tick={{ fontSize: 12 }} className="text-muted-foreground" />
              <YAxis tick={{ fontSize: 12 }} className="text-muted-foreground" />
              <Tooltip formatter={(value: number) => [Math.round(value), 'TSS']} />
              <Bar dataKey="tss" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
