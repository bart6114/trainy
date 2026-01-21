import { format } from 'date-fns'
import { Moon, Battery, Smile, Activity } from 'lucide-react'
import { useMorningCheckin, useWellnessSettings } from '@/hooks/useWellness'

export function WellnessSummary() {
  const today = format(new Date(), 'yyyy-MM-dd')
  const { data: settings } = useWellnessSettings()
  const { data: checkin, isLoading } = useMorningCheckin(today)

  // Don't show if wellness tracking is disabled
  if (!settings?.morning_checkin_enabled) {
    return null
  }

  // Don't show if no check-in yet
  if (isLoading || !checkin) {
    return null
  }

  const items: { icon: typeof Moon; label: string; value: string }[] = []

  if (checkin.sleep_hours !== null || checkin.sleep_quality !== null) {
    const parts = []
    if (checkin.sleep_hours !== null) parts.push(`${checkin.sleep_hours}h`)
    if (checkin.sleep_quality !== null) parts.push(`${checkin.sleep_quality}/10`)
    items.push({ icon: Moon, label: 'Sleep', value: parts.join(' · ') })
  }

  if (checkin.muscle_soreness !== null) {
    items.push({ icon: Activity, label: 'Soreness', value: `${checkin.muscle_soreness}/10` })
  }

  if (checkin.energy_level !== null) {
    items.push({ icon: Battery, label: 'Energy', value: `${checkin.energy_level}/10` })
  }

  if (checkin.mood !== null) {
    items.push({ icon: Smile, label: 'Mood', value: `${checkin.mood}/10` })
  }

  if (items.length === 0) {
    return null
  }

  return (
    <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-xs text-muted-foreground">
      <span className="font-medium text-foreground/70">Today:</span>
      {items.map((item, i) => (
        <div key={i} className="flex items-center gap-1">
          <item.icon className="h-3 w-3" />
          <span>{item.label}</span>
          <span className="font-medium text-foreground/80">{item.value}</span>
        </div>
      ))}
    </div>
  )
}
