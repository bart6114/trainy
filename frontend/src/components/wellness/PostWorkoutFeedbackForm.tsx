import { useState } from 'react'
import { format } from 'date-fns'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useWellnessSettings, useSubmitActivityFeedback } from '@/hooks/useWellness'
import type { PendingActivityItem } from '@/types'

interface PostWorkoutFeedbackFormProps {
  activity: PendingActivityItem | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

const RPE_LABELS: Record<number, string> = {
  1: 'Very Light',
  2: 'Light',
  3: 'Light',
  4: 'Moderate',
  5: 'Moderate',
  6: 'Somewhat Hard',
  7: 'Hard',
  8: 'Very Hard',
  9: 'Very Hard',
  10: 'Maximal',
}

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) {
    return `${hours}h ${minutes}m`
  }
  return `${minutes}m`
}

function formatDistance(meters: number | null): string {
  if (!meters) return ''
  const km = meters / 1000
  return `${km.toFixed(1)} km`
}

export function PostWorkoutFeedbackForm({
  activity,
  open,
  onOpenChange,
}: PostWorkoutFeedbackFormProps) {
  const { data: settings } = useWellnessSettings()
  const submitFeedback = useSubmitActivityFeedback()

  const [rpe, setRpe] = useState<number>(5)
  const [sessionFeel, setSessionFeel] = useState<number>(5)
  const [hasPain, setHasPain] = useState(false)
  const [painLocation, setPainLocation] = useState('')
  const [painSeverity, setPainSeverity] = useState<number>(3)
  const [notes, setNotes] = useState('')

  const handleSubmit = async () => {
    if (!activity) return

    await submitFeedback.mutateAsync({
      activityId: activity.id,
      data: {
        rpe: settings?.post_workout_rpe_enabled ? rpe : null,
        comfort_level: settings?.post_workout_session_feel_enabled ? sessionFeel : null,
        has_pain: settings?.post_workout_pain_enabled ? hasPain : false,
        pain_location: hasPain && settings?.post_workout_pain_enabled ? painLocation || null : null,
        pain_severity: hasPain && settings?.post_workout_pain_enabled ? painSeverity : null,
        notes: settings?.post_workout_notes_enabled && notes ? notes : null,
      },
    })
    onOpenChange(false)
    // Reset form
    setRpe(5)
    setSessionFeel(5)
    setHasPain(false)
    setPainLocation('')
    setPainSeverity(3)
    setNotes('')
  }

  if (!activity) return null

  const hasAnyMetricEnabled =
    settings?.post_workout_rpe_enabled ||
    settings?.post_workout_session_feel_enabled ||
    settings?.post_workout_pain_enabled ||
    settings?.post_workout_notes_enabled

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Post-Workout Feedback</DialogTitle>
          <DialogDescription>
            {activity.title || `${activity.activity_type} activity`}
          </DialogDescription>
        </DialogHeader>

        {/* Activity Summary */}
        <div className="rounded-lg bg-muted p-3 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Date</span>
            <span>{format(new Date(activity.start_time), 'MMM d, yyyy')}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Type</span>
            <span className="capitalize">{activity.activity_type}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Duration</span>
            <span>{formatDuration(activity.duration_seconds)}</span>
          </div>
          {activity.distance_meters && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Distance</span>
              <span>{formatDistance(activity.distance_meters)}</span>
            </div>
          )}
        </div>

        <div className="space-y-6 py-2">
          {settings?.post_workout_rpe_enabled && (
            <div className="space-y-3">
              <div className="flex justify-between">
                <Label>RPE (Rate of Perceived Exertion)</Label>
                <span className="text-sm font-medium">
                  {rpe} - {RPE_LABELS[rpe]}
                </span>
              </div>
              <Slider
                value={[rpe]}
                onValueChange={([v]) => setRpe(v)}
                min={1}
                max={10}
                step={1}
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Easy</span>
                <span>Maximal</span>
              </div>
            </div>
          )}

          {settings?.post_workout_session_feel_enabled && (
            <div className="space-y-3">
              <div className="flex justify-between">
                <Label>Session Feel</Label>
                <span className="text-sm font-medium">{sessionFeel}/10</span>
              </div>
              <Slider
                value={[sessionFeel]}
                onValueChange={([v]) => setSessionFeel(v)}
                min={1}
                max={10}
                step={1}
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Terrible</span>
                <span>Amazing</span>
              </div>
            </div>
          )}

          {settings?.post_workout_pain_enabled && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label>Any pain or discomfort?</Label>
                <Switch checked={hasPain} onCheckedChange={setHasPain} />
              </div>

              {hasPain && (
                <div className="space-y-3 pl-4 border-l-2 border-muted">
                  <div className="space-y-2">
                    <Label className="text-sm">Location</Label>
                    <Input
                      placeholder="e.g., Left knee, Lower back"
                      value={painLocation}
                      onChange={(e) => setPainLocation(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <Label className="text-sm">Severity</Label>
                      <span className="text-sm">{painSeverity}/10</span>
                    </div>
                    <Slider
                      value={[painSeverity]}
                      onValueChange={([v]) => setPainSeverity(v)}
                      min={1}
                      max={10}
                      step={1}
                    />
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>Mild</span>
                      <span>Severe</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {settings?.post_workout_notes_enabled && (
            <div className="space-y-2">
              <Label>Notes (optional)</Label>
              <Textarea
                placeholder="How did the workout feel? Any observations?"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={2}
              />
            </div>
          )}

          {!hasAnyMetricEnabled && (
            <p className="text-sm text-muted-foreground text-center py-4">
              No feedback metrics enabled. Enable metrics in Settings.
            </p>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Skip
          </Button>
          <Button onClick={handleSubmit} disabled={submitFeedback.isPending}>
            {submitFeedback.isPending ? 'Saving...' : 'Submit'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
