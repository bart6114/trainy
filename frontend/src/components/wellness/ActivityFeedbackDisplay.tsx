import { Gauge, Frown, AlertTriangle } from 'lucide-react'
import { useActivityFeedback } from '@/hooks/useWellness'

interface ActivityFeedbackDisplayProps {
  activityId: number
}

export function ActivityFeedbackDisplay({ activityId }: ActivityFeedbackDisplayProps) {
  const { data: feedback } = useActivityFeedback(activityId)

  if (!feedback) {
    return null
  }

  const items: { icon: typeof Gauge; value: string; color?: string }[] = []

  if (feedback.rpe !== null) {
    items.push({
      icon: Gauge,
      value: `RPE ${feedback.rpe}`,
      color: feedback.rpe >= 8 ? 'text-red-500' : feedback.rpe >= 6 ? 'text-amber-500' : 'text-green-500'
    })
  }

  if (feedback.comfort_level !== null) {
    items.push({
      icon: Frown,
      value: `Feel ${feedback.comfort_level}/10`,
      color: feedback.comfort_level <= 4 ? 'text-red-500' : feedback.comfort_level <= 6 ? 'text-amber-500' : 'text-green-500'
    })
  }

  if (feedback.has_pain && feedback.pain_location) {
    items.push({
      icon: AlertTriangle,
      value: `${feedback.pain_location}${feedback.pain_severity ? ` (${feedback.pain_severity}/10)` : ''}`,
      color: 'text-red-500'
    })
  }

  if (items.length === 0) {
    return null
  }

  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs mt-1">
      {items.map((item, i) => (
        <span key={i} className={`flex items-center gap-1 ${item.color || 'text-muted-foreground'}`}>
          <item.icon className="h-3 w-3" />
          {item.value}
        </span>
      ))}
    </div>
  )
}
