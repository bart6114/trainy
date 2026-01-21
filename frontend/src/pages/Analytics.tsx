import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { PowerCurveChart } from '@/components/charts/PowerCurveChart'
import { usePowerCurve } from '@/hooks/useAnalytics'
import { useProfile, useUpdateProfile } from '@/hooks/useProfile'
import { TrendingUp, TrendingDown, Minus, Settings, Save } from 'lucide-react'

const DATE_RANGES = [
  { value: 30, label: '30d' },
  { value: 90, label: '90d' },
  { value: 180, label: '6mo' },
  { value: 365, label: '1yr' },
]

export function Analytics() {
  const [days, setDays] = useState(90)
  const [showWattsPerKg, setShowWattsPerKg] = useState(false)

  const { data, isLoading, error, refetch } = usePowerCurve(days)
  const { data: profile } = useProfile()
  const updateProfile = useUpdateProfile()

  const ftp = profile?.ftp
  const ftpDiff = data?.eftp && ftp ? data.eftp - ftp : null
  const ftpDiffPercent = data?.eftp && ftp ? ((data.eftp - ftp) / ftp * 100) : null

  const handleSaveEftpAsFtp = async () => {
    if (data?.eftp) {
      await updateProfile.mutateAsync({ ftp: data.eftp })
      refetch()
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
          <p className="text-muted-foreground">Power curve and performance analysis</p>
        </div>
        <div className="flex gap-2">
          {DATE_RANGES.map((range) => (
            <Button
              key={range.value}
              variant={days === range.value ? 'default' : 'outline'}
              size="sm"
              onClick={() => setDays(range.value)}
            >
              {range.label}
            </Button>
          ))}
        </div>
      </div>

      {/* eFTP Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Estimated FTP (eFTP)</CardDescription>
            <CardTitle className="text-3xl">
              {isLoading ? '...' : data?.eftp ? `${data.eftp} W` : 'No data'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">
              {data?.eftp_method === 'morton_3p'
                ? 'Critical power from power-duration model'
                : `95% of best 20-min power in the last ${days} days`}
            </p>
          </CardContent>
        </Card>

        {data?.w_prime && (
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>W' (Anaerobic Capacity)</CardDescription>
              <CardTitle className="text-3xl">
                {(data.w_prime / 1000).toFixed(1)} kJ
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                Work available above threshold
              </p>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Current FTP</CardDescription>
            <CardTitle className="text-3xl">
              {ftp ? `${ftp} W` : 'Not set'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Link to="/settings" className="text-xs text-blue-600 hover:underline flex items-center gap-1">
              <Settings className="h-3 w-3" />
              Update in Settings
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>eFTP vs FTP</CardDescription>
            <CardTitle className="text-3xl flex items-center gap-2">
              {isLoading ? (
                '...'
              ) : ftpDiff !== null ? (
                <>
                  {ftpDiff > 0 ? (
                    <TrendingUp className="h-6 w-6 text-green-600" />
                  ) : ftpDiff < 0 ? (
                    <TrendingDown className="h-6 w-6 text-red-600" />
                  ) : (
                    <Minus className="h-6 w-6 text-gray-500" />
                  )}
                  <span className={ftpDiff > 0 ? 'text-green-600' : ftpDiff < 0 ? 'text-red-600' : ''}>
                    {ftpDiff > 0 ? '+' : ''}{ftpDiff} W
                  </span>
                </>
              ) : (
                'N/A'
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <p className="text-xs text-muted-foreground">
              {ftpDiffPercent !== null
                ? `${ftpDiffPercent > 0 ? '+' : ''}${ftpDiffPercent.toFixed(1)}% ${ftpDiff && ftpDiff > 0 ? 'above' : ftpDiff && ftpDiff < 0 ? 'below' : 'equal to'} your set FTP`
                : 'Compare your estimated vs configured FTP'}
            </p>
            {data?.eftp && ftpDiff !== 0 && (
              <Button
                size="sm"
                variant="outline"
                className="w-full"
                onClick={handleSaveEftpAsFtp}
                disabled={updateProfile.isPending}
              >
                <Save className="h-3 w-3 mr-1" />
                {updateProfile.isPending ? 'Saving...' : `Set FTP to ${data.eftp} W`}
              </Button>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Power Curve Chart */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Power Curve</CardTitle>
              <CardDescription>
                Best power outputs at key durations
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant={!showWattsPerKg ? 'default' : 'outline'}
                size="sm"
                onClick={() => setShowWattsPerKg(false)}
              >
                Watts
              </Button>
              <Button
                variant={showWattsPerKg ? 'default' : 'outline'}
                size="sm"
                onClick={() => setShowWattsPerKg(true)}
              >
                W/kg
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="h-[300px] flex items-center justify-center text-muted-foreground">
              Loading power data...
            </div>
          ) : error ? (
            <div className="h-[300px] flex items-center justify-center text-red-500">
              Error loading data
            </div>
          ) : data?.points ? (
            <PowerCurveChart data={data.points} showWattsPerKg={showWattsPerKg} />
          ) : (
            <div className="h-[300px] flex items-center justify-center text-muted-foreground">
              No power data available
            </div>
          )}
        </CardContent>
      </Card>

      {/* Peak Power Values Grid */}
      {data?.points && data.points.some(p => p.best_watts !== null) && (
        <Card>
          <CardHeader>
            <CardTitle>Peak Power Values</CardTitle>
            <CardDescription>
              Your best power outputs over the last {days} days
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {data.points.map((point) => (
                <div key={point.duration_seconds} className="text-center p-4 bg-muted rounded-lg">
                  <div className="text-sm font-medium text-muted-foreground mb-1">
                    {point.duration_label}
                  </div>
                  <div className="text-2xl font-bold">
                    {point.best_watts !== null ? (
                      showWattsPerKg
                        ? `${point.best_watts_per_kg?.toFixed(2)} W/kg`
                        : `${Math.round(point.best_watts)} W`
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </div>
                  {point.activity_date && (
                    <div className="text-xs text-muted-foreground mt-1">
                      {point.activity_date}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
