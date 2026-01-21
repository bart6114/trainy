import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface MetricsCardProps {
  title: string
  value: string | number
  subtitle?: string
  badge?: {
    label: string
    className?: string
  }
  trend?: {
    value: number
    label: string
  }
}

export function MetricsCard({ title, value, subtitle, badge, trend }: MetricsCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {badge && (
          <Badge className={badge.className} variant="secondary">
            {badge.label}
          </Badge>
        )}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
        {trend && (
          <p className={cn('text-xs', trend.value >= 0 ? 'text-green-600' : 'text-red-600')}>
            {trend.value >= 0 ? '+' : ''}{trend.value} {trend.label}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
