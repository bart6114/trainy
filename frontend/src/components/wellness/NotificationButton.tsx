import { useState } from 'react'
import { Bell, Sun, Activity } from 'lucide-react'
import { format } from 'date-fns'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { usePendingFeedback } from '@/hooks/useWellness'
import { MorningCheckinForm } from './MorningCheckinForm'
import { PostWorkoutFeedbackForm } from './PostWorkoutFeedbackForm'
import type { PendingActivityItem } from '@/types'

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) {
    return `${hours}h ${minutes}m`
  }
  return `${minutes}m`
}

export function NotificationButton() {
  const { data: pending } = usePendingFeedback()
  const [popoverOpen, setPopoverOpen] = useState(false)
  const [morningCheckinOpen, setMorningCheckinOpen] = useState(false)
  const [feedbackActivity, setFeedbackActivity] = useState<PendingActivityItem | null>(null)

  const count = pending?.total_count ?? 0

  const handleMorningCheckin = () => {
    setPopoverOpen(false)
    setMorningCheckinOpen(true)
  }

  const handleActivityFeedback = (activity: PendingActivityItem) => {
    setPopoverOpen(false)
    setFeedbackActivity(activity)
  }

  if (count === 0) {
    return null
  }

  return (
    <>
      <Popover open={popoverOpen} onOpenChange={setPopoverOpen}>
        <PopoverTrigger asChild>
          <Button variant="ghost" size="icon" className="relative">
            <Bell className="h-5 w-5" />
            {count > 0 && (
              <Badge
                variant="destructive"
                className="absolute -right-1 -top-1 h-5 w-5 rounded-full p-0 text-xs flex items-center justify-center"
              >
                {count > 9 ? '9+' : count}
              </Badge>
            )}
            <span className="sr-only">Pending wellness items</span>
          </Button>
        </PopoverTrigger>
        <PopoverContent align="end" className="w-80">
          <div className="space-y-2">
            <h4 className="font-medium text-sm">Pending Items</h4>

            {pending?.morning_checkin_pending && (
              <button
                onClick={handleMorningCheckin}
                className="w-full flex items-center gap-3 rounded-lg border p-3 text-left hover:bg-accent transition-colors"
              >
                <div className="rounded-full bg-amber-100 p-2 text-amber-600">
                  <Sun className="h-4 w-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">Morning Check-in</p>
                  <p className="text-xs text-muted-foreground">
                    {format(new Date(), 'EEEE, MMM d')}
                  </p>
                </div>
              </button>
            )}

            {pending?.activities.map((activity) => (
              <button
                key={activity.id}
                onClick={() => handleActivityFeedback(activity)}
                className="w-full flex items-center gap-3 rounded-lg border p-3 text-left hover:bg-accent transition-colors"
              >
                <div className="rounded-full bg-blue-100 p-2 text-blue-600">
                  <Activity className="h-4 w-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">
                    {activity.title || `${activity.activity_type} activity`}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {format(new Date(activity.start_time), 'MMM d')} &middot;{' '}
                    {formatDuration(activity.duration_seconds)}
                  </p>
                </div>
              </button>
            ))}

            {count === 0 && (
              <p className="text-sm text-muted-foreground text-center py-4">
                All caught up!
              </p>
            )}
          </div>
        </PopoverContent>
      </Popover>

      <MorningCheckinForm
        open={morningCheckinOpen}
        onOpenChange={setMorningCheckinOpen}
      />

      <PostWorkoutFeedbackForm
        activity={feedbackActivity}
        open={!!feedbackActivity}
        onOpenChange={(open) => {
          if (!open) setFeedbackActivity(null)
        }}
      />
    </>
  )
}
