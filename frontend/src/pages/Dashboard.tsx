import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Info } from 'lucide-react'
import { ActivityCalendar } from '@/components/calendar/ActivityCalendar'
import { DateActivitiesPanel } from '@/components/calendar/DateActivitiesPanel'
import { MetricsCard } from '@/components/metrics/MetricsCard'
import { useCurrentMetrics } from '@/hooks/useMetrics'
import { useActivities } from '@/hooks/useActivities'
import { ActivityCard } from '@/components/activities/ActivityCard'
import { getFormStatusColor, getACWRStatusColor } from '@/lib/utils'
import { Button } from '@/components/ui/button'

export function Dashboard() {
  const [selectedDate, setSelectedDate] = useState<Date | null>(null)
  const { data: metrics, isLoading: metricsLoading } = useCurrentMetrics()
  const { data: activities, isLoading: activitiesLoading } = useActivities(0, 5)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">Your training overview</p>
      </div>

      {/* Metrics Cards */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Training Metrics</h2>
        <Button variant="ghost" size="sm" asChild>
          <Link to="/metrics" className="text-muted-foreground hover:text-foreground">
            <Info className="h-4 w-4 mr-1" />
            Learn more
          </Link>
        </Button>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricsCard
          title="Fitness (CTL)"
          value={metricsLoading ? '...' : Math.round(metrics?.ctl || 0)}
          subtitle="Chronic Training Load"
        />
        <MetricsCard
          title="Fatigue (ATL)"
          value={metricsLoading ? '...' : Math.round(metrics?.atl || 0)}
          subtitle="Acute Training Load"
        />
        <MetricsCard
          title="Form (TSB)"
          value={metricsLoading ? '...' : Math.round(metrics?.tsb || 0)}
          subtitle="Training Stress Balance"
          badge={metrics ? { label: metrics.form_status, className: getFormStatusColor(metrics.form_status) } : undefined}
        />
        <MetricsCard
          title="ACWR"
          value={metricsLoading ? '...' : (metrics?.acwr?.toFixed(2) || 'N/A')}
          subtitle="Acute:Chronic Workload"
          badge={metrics?.acwr_status ? { label: metrics.acwr_status, className: getACWRStatusColor(metrics.acwr_status) } : undefined}
        />
      </div>

      {/* Advanced Metrics */}
      <div className="grid gap-4 md:grid-cols-3">
        <MetricsCard
          title="7-Day TSS"
          value={metricsLoading ? '...' : Math.round(metrics?.tss_7day || 0)}
          subtitle="Last 7 days"
        />
        <MetricsCard
          title="Monotony"
          value={metricsLoading ? '...' : (metrics?.monotony?.toFixed(2) || 'N/A')}
          subtitle={metrics?.monotony && metrics.monotony > 2.0 ? "High - Vary training!" : "Training variation"}
        />
        <MetricsCard
          title="Strain"
          value={metricsLoading ? '...' : (metrics?.strain ? Math.round(metrics.strain) : 'N/A')}
          subtitle={metrics?.strain && metrics.strain > 6000 ? "Very High - Monitor recovery" : "Weekly load x monotony"}
        />
      </div>

      {/* Calendar and Activities */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <ActivityCalendar onDateSelect={setSelectedDate} />
        </div>
        <div>
          <DateActivitiesPanel date={selectedDate} />
        </div>
      </div>

      {/* Recent Activities */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Recent Activities</h2>
        {activitiesLoading ? (
          <p className="text-muted-foreground">Loading activities...</p>
        ) : activities && activities.items.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {activities.items.map((activity) => (
              <ActivityCard key={activity.id} activity={activity} />
            ))}
          </div>
        ) : (
          <p className="text-muted-foreground">No activities yet. Import some FIT files to get started!</p>
        )}
      </div>
    </div>
  )
}
