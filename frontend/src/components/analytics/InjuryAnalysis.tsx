import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { PainTimelineChart } from '@/components/charts/PainTimelineChart'
import { ManageLocationsModal } from '@/components/analytics/ManageLocationsModal'
import { useInjuryAnalysis } from '@/hooks/useAnalytics'
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, Cell } from 'recharts'
import { AlertCircle, MapPin, Activity, Settings } from 'lucide-react'

interface InjuryAnalysisProps {
  days: number
}

// Colors for bar charts
const BAR_COLORS = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6', '#8b5cf6']

export function InjuryAnalysis({ days }: InjuryAnalysisProps) {
  const { data, isLoading, error } = useInjuryAnalysis(days)
  const [manageLocationsOpen, setManageLocationsOpen] = useState(false)

  if (isLoading) {
    return (
      <div className="h-[400px] flex items-center justify-center text-muted-foreground">
        Loading injury analysis...
      </div>
    )
  }

  if (error) {
    return (
      <div className="h-[400px] flex items-center justify-center text-red-500">
        Error loading injury data
      </div>
    )
  }

  // Empty state
  if (!data || data.total_pain_events === 0) {
    return (
      <Card>
        <CardContent className="py-12">
          <div className="text-center space-y-4">
            <AlertCircle className="h-12 w-12 mx-auto text-muted-foreground" />
            <div>
              <h3 className="text-lg font-medium">No pain data recorded yet</h3>
              <p className="text-sm text-muted-foreground mt-1">
                Enable pain tracking in{' '}
                <Link to="/settings" className="text-blue-600 hover:underline inline-flex items-center gap-1">
                  <Settings className="h-3 w-3" />
                  Settings &gt; Wellness Tracking
                </Link>
                {' '}to start monitoring injuries.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  const mostAffectedLocation = data.by_location[0]
  const avgSeverity = data.pain_events.length > 0
    ? (data.pain_events.reduce((sum, e) => sum + (e.pain_severity || 0), 0) / data.pain_events.length).toFixed(1)
    : '0'

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-1">
              <AlertCircle className="h-3 w-3" />
              Total Pain Events
            </CardDescription>
            <CardTitle className="text-3xl">{data.total_pain_events}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">
              In the last {days} days
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-1">
              <MapPin className="h-3 w-3" />
              Most Affected
            </CardDescription>
            <CardTitle className="text-3xl capitalize">
              {mostAffectedLocation?.location || 'N/A'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">
              {mostAffectedLocation ? `${mostAffectedLocation.count} occurrences` : 'No data'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-1">
              <Activity className="h-3 w-3" />
              Avg Severity
            </CardDescription>
            <CardTitle className="text-3xl">{avgSeverity}/10</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">
              Across all pain events
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Pain Timeline Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Pain Timeline</CardTitle>
          <CardDescription>
            Pain events over time, colored by body location
          </CardDescription>
        </CardHeader>
        <CardContent>
          <PainTimelineChart data={data.pain_events} />
        </CardContent>
      </Card>

      {/* By Location and By Activity Charts */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-start justify-between space-y-0">
            <div>
              <CardTitle>By Location</CardTitle>
              <CardDescription>Pain occurrences by body part</CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setManageLocationsOpen(true)}
            >
              Manage Locations
            </Button>
          </CardHeader>
          <CardContent>
            {data.by_location.length > 0 ? (
              <div className="h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={data.by_location}
                    layout="vertical"
                    margin={{ top: 5, right: 30, left: 60, bottom: 5 }}
                  >
                    <XAxis type="number" tick={{ fontSize: 11 }} />
                    <YAxis
                      dataKey="location"
                      type="category"
                      tick={{ fontSize: 11 }}
                      tickFormatter={(v) => v ? v.charAt(0).toUpperCase() + v.slice(1) : 'Unknown'}
                    />
                    <Tooltip
                      formatter={(value: number) => [`${value}`, 'Count']}
                      labelFormatter={(label) => {
                        const item = data.by_location.find(l => l.location === label)
                        return `${label ? label.charAt(0).toUpperCase() + label.slice(1) : 'Unknown'} (avg: ${item?.avg_severity ?? 'N/A'}/10)`
                      }}
                    />
                    <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                      {data.by_location.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={BAR_COLORS[index % BAR_COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-[200px] flex items-center justify-center text-muted-foreground">
                No location data
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>By Activity Type</CardTitle>
            <CardDescription>Pain occurrences by activity</CardDescription>
          </CardHeader>
          <CardContent>
            {data.by_activity.length > 0 ? (
              <div className="h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={data.by_activity}
                    margin={{ top: 5, right: 30, left: 20, bottom: 30 }}
                  >
                    <XAxis
                      dataKey="activity_type"
                      tick={{ fontSize: 11 }}
                      tickFormatter={(v) => v ? v.charAt(0).toUpperCase() + v.slice(1) : 'Unknown'}
                      angle={-45}
                      textAnchor="end"
                    />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip
                      formatter={(value: number) => [`${value}`, 'Count']}
                      labelFormatter={(label) => {
                        const item = data.by_activity.find(a => a.activity_type === label)
                        return `${label ? label.charAt(0).toUpperCase() + label.slice(1) : 'Unknown'} (avg: ${item?.avg_severity ?? 'N/A'}/10)`
                      }}
                    />
                    <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]}>
                      {data.by_activity.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={BAR_COLORS[index % BAR_COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-[200px] flex items-center justify-center text-muted-foreground">
                No activity data
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Pain Entries */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Pain Entries</CardTitle>
          <CardDescription>Last {Math.min(10, data.pain_events.length)} pain events</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {data.pain_events.slice(0, 10).map((event, index) => (
              <div
                key={`${event.activity_id}-${index}`}
                className="flex items-center justify-between py-2 border-b last:border-0"
              >
                <div className="flex items-center gap-3">
                  <div className="text-sm text-muted-foreground w-20">
                    {new Date(event.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  </div>
                  <div>
                    <span className="font-medium capitalize">{event.pain_location || 'Unknown'}</span>
                    <span className="text-muted-foreground"> - </span>
                    <span className="capitalize text-sm">{event.activity_type}</span>
                    {event.activity_title && (
                      <span className="text-xs text-muted-foreground ml-2">({event.activity_title})</span>
                    )}
                  </div>
                </div>
                <div className="text-sm font-medium">
                  <span className={event.pain_severity && event.pain_severity >= 7 ? 'text-red-600' : event.pain_severity && event.pain_severity >= 4 ? 'text-orange-500' : ''}>
                    {event.pain_severity}/10
                  </span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <ManageLocationsModal
        open={manageLocationsOpen}
        onOpenChange={setManageLocationsOpen}
      />
    </div>
  )
}
