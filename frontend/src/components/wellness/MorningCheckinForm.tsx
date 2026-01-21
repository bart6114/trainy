import { useState } from 'react'
import { format } from 'date-fns'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useWellnessSettings, useSubmitMorningCheckin } from '@/hooks/useWellness'

interface MorningCheckinFormProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

const SCALE_LABELS: Record<string, { low: string; high: string }> = {
  sleep_quality: { low: 'Poor', high: 'Excellent' },
  muscle_soreness: { low: 'None', high: 'Severe' },
  energy_level: { low: 'Exhausted', high: 'Energized' },
  mood: { low: 'Low', high: 'Great' },
}

export function MorningCheckinForm({ open, onOpenChange }: MorningCheckinFormProps) {
  const { data: settings } = useWellnessSettings()
  const submitCheckin = useSubmitMorningCheckin()

  const [sleepQuality, setSleepQuality] = useState<number>(5)
  const [sleepHours, setSleepHours] = useState<number>(7)
  const [muscleSoreness, setMuscleSoreness] = useState<number>(3)
  const [energyLevel, setEnergyLevel] = useState<number>(5)
  const [mood, setMood] = useState<number>(5)
  const [notes, setNotes] = useState('')

  const today = format(new Date(), 'yyyy-MM-dd')

  const handleSubmit = async () => {
    await submitCheckin.mutateAsync({
      checkin_date: today,
      sleep_quality: settings?.morning_sleep_quality_enabled ? sleepQuality : null,
      sleep_hours: settings?.morning_sleep_hours_enabled ? sleepHours : null,
      muscle_soreness: settings?.morning_muscle_soreness_enabled ? muscleSoreness : null,
      energy_level: settings?.morning_energy_enabled ? energyLevel : null,
      mood: settings?.morning_mood_enabled ? mood : null,
      notes: notes || null,
    })
    onOpenChange(false)
  }

  const hasAnyMetricEnabled =
    settings?.morning_sleep_quality_enabled ||
    settings?.morning_sleep_hours_enabled ||
    settings?.morning_muscle_soreness_enabled ||
    settings?.morning_energy_enabled ||
    settings?.morning_mood_enabled

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Morning Check-in</DialogTitle>
          <DialogDescription>
            {format(new Date(), 'EEEE, MMMM d, yyyy')}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {settings?.morning_sleep_quality_enabled && (
            <div className="space-y-3">
              <div className="flex justify-between">
                <Label>Sleep Quality</Label>
                <span className="text-sm font-medium">{sleepQuality}/10</span>
              </div>
              <Slider
                value={[sleepQuality]}
                onValueChange={([v]) => setSleepQuality(v)}
                min={1}
                max={10}
                step={1}
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>{SCALE_LABELS.sleep_quality.low}</span>
                <span>{SCALE_LABELS.sleep_quality.high}</span>
              </div>
            </div>
          )}

          {settings?.morning_sleep_hours_enabled && (
            <div className="space-y-3">
              <div className="flex justify-between">
                <Label>Sleep Duration</Label>
                <span className="text-sm font-medium">{sleepHours}h</span>
              </div>
              <Slider
                value={[sleepHours]}
                onValueChange={([v]) => setSleepHours(v)}
                min={0}
                max={12}
                step={0.5}
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>0h</span>
                <span>12h</span>
              </div>
            </div>
          )}

          {settings?.morning_muscle_soreness_enabled && (
            <div className="space-y-3">
              <div className="flex justify-between">
                <Label>Muscle Soreness</Label>
                <span className="text-sm font-medium">{muscleSoreness}/10</span>
              </div>
              <Slider
                value={[muscleSoreness]}
                onValueChange={([v]) => setMuscleSoreness(v)}
                min={1}
                max={10}
                step={1}
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>{SCALE_LABELS.muscle_soreness.low}</span>
                <span>{SCALE_LABELS.muscle_soreness.high}</span>
              </div>
            </div>
          )}

          {settings?.morning_energy_enabled && (
            <div className="space-y-3">
              <div className="flex justify-between">
                <Label>Energy Level</Label>
                <span className="text-sm font-medium">{energyLevel}/10</span>
              </div>
              <Slider
                value={[energyLevel]}
                onValueChange={([v]) => setEnergyLevel(v)}
                min={1}
                max={10}
                step={1}
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>{SCALE_LABELS.energy_level.low}</span>
                <span>{SCALE_LABELS.energy_level.high}</span>
              </div>
            </div>
          )}

          {settings?.morning_mood_enabled && (
            <div className="space-y-3">
              <div className="flex justify-between">
                <Label>Mood</Label>
                <span className="text-sm font-medium">{mood}/10</span>
              </div>
              <Slider
                value={[mood]}
                onValueChange={([v]) => setMood(v)}
                min={1}
                max={10}
                step={1}
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>{SCALE_LABELS.mood.low}</span>
                <span>{SCALE_LABELS.mood.high}</span>
              </div>
            </div>
          )}

          {!hasAnyMetricEnabled && (
            <p className="text-sm text-muted-foreground text-center py-4">
              No metrics enabled. Enable metrics in Settings to track your wellness.
            </p>
          )}

          <div className="space-y-2">
            <Label>Notes (optional)</Label>
            <Textarea
              placeholder="How are you feeling today?"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={submitCheckin.isPending}>
            {submitCheckin.isPending ? 'Saving...' : 'Save'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
