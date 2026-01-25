import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useRowingPRs } from '@/hooks/useAnalytics'

/**
 * Format seconds to MM:SS.s or HH:MM:SS format
 */
function formatTime(seconds: number): string {
  if (seconds < 3600) {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toFixed(1).padStart(4, '0')}`
  }
  const hours = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

/**
 * Format split time (per 500m) in standard rowing format
 */
function formatSplit(splitSeconds: number): string {
  const mins = Math.floor(splitSeconds / 60)
  const secs = splitSeconds % 60
  return `${mins}:${secs.toFixed(1).padStart(4, '0')}/500m`
}

/**
 * Format distance in meters
 */
function formatDistance(meters: number): string {
  if (meters >= 1000) {
    return `${(meters / 1000).toFixed(2)}k`
  }
  return `${Math.round(meters)}m`
}

/**
 * Format date as "Jan 5" style
 */
function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

interface RowingPRsProps {
  days?: number
}

export function RowingPRs({ days = 90 }: RowingPRsProps) {
  const { data, isLoading, error } = useRowingPRs(days)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        Loading rowing PRs...
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 text-red-500">
        Error loading rowing data
      </div>
    )
  }

  const hasDistancePRs = data?.distance_prs.some(pr => pr.total_seconds !== null)
  const hasTimePRs = data?.time_prs.some(pr => pr.best_distance_meters !== null)
  const hasPowerPRs = data?.power_prs.some(pr => pr.best_watts !== null)

  if (!hasDistancePRs && !hasTimePRs && !hasPowerPRs) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        No rowing data available. Import rowing activities to see your PRs.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Distance PRs */}
      <Card>
        <CardHeader>
          <CardTitle>Distance PRs</CardTitle>
          <CardDescription>
            Best times at standard rowing distances
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {data?.distance_prs.map((pr) => (
              <div
                key={pr.distance_meters}
                className="text-center p-4 bg-muted rounded-lg"
              >
                <div className="text-sm font-medium text-muted-foreground mb-1">
                  {pr.distance_label}
                </div>
                {pr.total_seconds !== null ? (
                  <>
                    <div className="text-2xl font-bold">
                      {formatTime(pr.total_seconds)}
                    </div>
                    {pr.split_seconds !== null && (
                      <div className="text-sm text-muted-foreground">
                        {formatSplit(pr.split_seconds)}
                      </div>
                    )}
                    {pr.activity_date && (
                      <div className="text-xs text-muted-foreground mt-1">
                        {formatDate(pr.activity_date)}
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-2xl font-bold text-muted-foreground">-</div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Time PRs */}
      <Card>
        <CardHeader>
          <CardTitle>Time PRs</CardTitle>
          <CardDescription>
            Best distance covered at standard durations
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
            {data?.time_prs.map((pr) => (
              <div
                key={pr.duration_seconds}
                className="text-center p-4 bg-muted rounded-lg"
              >
                <div className="text-sm font-medium text-muted-foreground mb-1">
                  {pr.duration_label}
                </div>
                {pr.best_distance_meters !== null ? (
                  <>
                    <div className="text-2xl font-bold">
                      {formatDistance(pr.best_distance_meters)}
                    </div>
                    {pr.split_seconds !== null && (
                      <div className="text-sm text-muted-foreground">
                        {formatSplit(pr.split_seconds)}
                      </div>
                    )}
                    {pr.activity_date && (
                      <div className="text-xs text-muted-foreground mt-1">
                        {formatDate(pr.activity_date)}
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-2xl font-bold text-muted-foreground">-</div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Power PRs */}
      <Card>
        <CardHeader>
          <CardTitle>Power PRs</CardTitle>
          <CardDescription>
            Best average power at standard durations
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {data?.power_prs.map((pr) => (
              <div
                key={pr.duration_seconds}
                className="text-center p-4 bg-muted rounded-lg"
              >
                <div className="text-sm font-medium text-muted-foreground mb-1">
                  {pr.duration_label}
                </div>
                {pr.best_watts !== null ? (
                  <>
                    <div className="text-2xl font-bold">
                      {Math.round(pr.best_watts)} W
                    </div>
                    {pr.activity_date && (
                      <div className="text-xs text-muted-foreground mt-1">
                        {formatDate(pr.activity_date)}
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-2xl font-bold text-muted-foreground">-</div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
