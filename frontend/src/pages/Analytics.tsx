import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { PowerAnalysis } from '@/components/analytics/PowerAnalysis'
import { InjuryAnalysis } from '@/components/analytics/InjuryAnalysis'
import { PerformanceAnalysis } from '@/components/analytics/PerformanceAnalysis'
import { TrainingLoad } from '@/components/analytics/TrainingLoad'
import { Zap, HeartPulse, TrendingUp, BarChart3 } from 'lucide-react'

const DATE_RANGES = [
  { value: 30, label: '30d' },
  { value: 90, label: '90d' },
  { value: 180, label: '6mo' },
  { value: 365, label: '1yr' },
]

type TabValue = 'performance' | 'training-load' | 'power' | 'injury'

export function Analytics() {
  const [days, setDays] = useState(90)
  const [focus, setFocus] = useState<TabValue>('performance')

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
          <p className="text-muted-foreground">Performance and wellness analysis</p>
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

      <Tabs value={focus} onValueChange={(v) => setFocus(v as TabValue)}>
        <TabsList>
          <TabsTrigger value="performance" className="gap-2">
            <TrendingUp className="h-4 w-4" />
            Performance
          </TabsTrigger>
          <TabsTrigger value="training-load" className="gap-2">
            <BarChart3 className="h-4 w-4" />
            Training Load
          </TabsTrigger>
          <TabsTrigger value="power" className="gap-2">
            <Zap className="h-4 w-4" />
            Power
          </TabsTrigger>
          <TabsTrigger value="injury" className="gap-2">
            <HeartPulse className="h-4 w-4" />
            Injury
          </TabsTrigger>
        </TabsList>

        <TabsContent value="performance">
          <PerformanceAnalysis days={days} />
        </TabsContent>

        <TabsContent value="training-load">
          <TrainingLoad days={days} />
        </TabsContent>

        <TabsContent value="power">
          <PowerAnalysis days={days} />
        </TabsContent>

        <TabsContent value="injury">
          <InjuryAnalysis days={days} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
