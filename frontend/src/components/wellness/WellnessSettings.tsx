import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { useWellnessSettings, useUpdateWellnessSettings } from '@/hooks/useWellness'

export function WellnessSettings() {
  const { data: settings, isLoading } = useWellnessSettings()
  const updateSettings = useUpdateWellnessSettings()

  const handleToggle = (key: string, value: boolean) => {
    updateSettings.mutate({ [key]: value })
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Wellness Tracking</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-muted-foreground">Loading...</div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Wellness Tracking</CardTitle>
        <CardDescription>
          Configure daily check-ins and post-workout feedback prompts
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Morning Check-in Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="morning-checkin" className="text-base font-medium">
                Morning Check-in
              </Label>
              <p className="text-sm text-muted-foreground">
                Daily wellness metrics before training
              </p>
            </div>
            <Switch
              id="morning-checkin"
              checked={settings?.morning_checkin_enabled ?? false}
              onCheckedChange={(checked) => handleToggle('morning_checkin_enabled', checked)}
            />
          </div>

          {settings?.morning_checkin_enabled && (
            <div className="ml-4 space-y-3 border-l-2 border-muted pl-4">
              <div className="flex items-center justify-between">
                <Label htmlFor="sleep-quality" className="text-sm">
                  Sleep Quality
                </Label>
                <Switch
                  id="sleep-quality"
                  checked={settings?.morning_sleep_quality_enabled ?? false}
                  onCheckedChange={(checked) => handleToggle('morning_sleep_quality_enabled', checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="sleep-hours" className="text-sm">
                  Sleep Hours
                </Label>
                <Switch
                  id="sleep-hours"
                  checked={settings?.morning_sleep_hours_enabled ?? false}
                  onCheckedChange={(checked) => handleToggle('morning_sleep_hours_enabled', checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="muscle-soreness" className="text-sm">
                  Muscle Soreness
                </Label>
                <Switch
                  id="muscle-soreness"
                  checked={settings?.morning_muscle_soreness_enabled ?? false}
                  onCheckedChange={(checked) => handleToggle('morning_muscle_soreness_enabled', checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="energy-level" className="text-sm">
                  Energy Level
                </Label>
                <Switch
                  id="energy-level"
                  checked={settings?.morning_energy_enabled ?? false}
                  onCheckedChange={(checked) => handleToggle('morning_energy_enabled', checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="mood" className="text-sm">
                  Mood
                </Label>
                <Switch
                  id="mood"
                  checked={settings?.morning_mood_enabled ?? false}
                  onCheckedChange={(checked) => handleToggle('morning_mood_enabled', checked)}
                />
              </div>
            </div>
          )}
        </div>

        {/* Post-Workout Feedback Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="post-workout" className="text-base font-medium">
                Post-Workout Feedback
              </Label>
              <p className="text-sm text-muted-foreground">
                Feedback prompts after completing activities
              </p>
            </div>
            <Switch
              id="post-workout"
              checked={settings?.post_workout_feedback_enabled ?? false}
              onCheckedChange={(checked) => handleToggle('post_workout_feedback_enabled', checked)}
            />
          </div>

          {settings?.post_workout_feedback_enabled && (
            <div className="ml-4 space-y-3 border-l-2 border-muted pl-4">
              <div className="flex items-center justify-between">
                <Label htmlFor="rpe" className="text-sm">
                  RPE (Rate of Perceived Exertion)
                </Label>
                <Switch
                  id="rpe"
                  checked={settings?.post_workout_rpe_enabled ?? false}
                  onCheckedChange={(checked) => handleToggle('post_workout_rpe_enabled', checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="session-feel" className="text-sm">
                  Session Feel
                </Label>
                <Switch
                  id="session-feel"
                  checked={settings?.post_workout_session_feel_enabled ?? false}
                  onCheckedChange={(checked) => handleToggle('post_workout_session_feel_enabled', checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="pain-tracking" className="text-sm">
                  Pain/Injury Tracking
                </Label>
                <Switch
                  id="pain-tracking"
                  checked={settings?.post_workout_pain_enabled ?? false}
                  onCheckedChange={(checked) => handleToggle('post_workout_pain_enabled', checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="notes" className="text-sm">
                  Notes
                </Label>
                <Switch
                  id="notes"
                  checked={settings?.post_workout_notes_enabled ?? false}
                  onCheckedChange={(checked) => handleToggle('post_workout_notes_enabled', checked)}
                />
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
