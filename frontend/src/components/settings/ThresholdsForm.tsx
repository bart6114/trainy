import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { PaceInput } from '@/components/ui/pace-input'
import { useProfile, useUpdateProfile, useDetectMaxHR } from '@/hooks/useProfile'
import { useRecalculate } from '@/hooks/useRecalculate'

const profileSchema = z.object({
  ftp: z.coerce.number().min(50).max(500),
  lthr: z.coerce.number().min(100).max(220),
  max_hr: z.coerce.number().min(120).max(250),
  resting_hr: z.coerce.number().min(30).max(100),
  threshold_pace_minkm: z.coerce.number().min(2).max(15),
  swim_threshold_pace: z.coerce.number().min(0.5).max(5),
  weight_kg: z.coerce.number().min(30).max(200),
})

type ProfileFormData = z.infer<typeof profileSchema>

export function ThresholdsForm() {
  const { data: profile, isLoading } = useProfile()
  const updateProfile = useUpdateProfile()
  const detectMaxHR = useDetectMaxHR()
  const {
    isRunning: isRecalculating,
    progress,
    total,
    phase,
    currentItem,
    activitiesProcessed,
    daysProcessed,
    totalActivities,
    totalDays,
    startRecalculate,
    cancelRecalculate,
  } = useRecalculate()

  const { register, handleSubmit, setValue, control, formState: { errors, isDirty } } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    values: profile ? {
      ftp: profile.ftp,
      lthr: profile.lthr,
      max_hr: profile.max_hr,
      resting_hr: profile.resting_hr,
      threshold_pace_minkm: profile.threshold_pace_minkm,
      swim_threshold_pace: profile.swim_threshold_pace,
      weight_kg: profile.weight_kg,
    } : undefined,
  })

  const onSubmit = async (data: ProfileFormData) => {
    await updateProfile.mutateAsync(data)
  }

  const handleDetectMaxHR = async () => {
    const result = await detectMaxHR.mutateAsync()
    if (result.detected_max_hr) {
      setValue('max_hr', result.detected_max_hr, { shouldDirty: true })
    }
  }

  const handleRecalculate = () => {
    startRecalculate()
  }

  if (isLoading) {
    return <div className="text-muted-foreground">Loading profile...</div>
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Training Thresholds</CardTitle>
        <CardDescription>
          Configure your personal thresholds for accurate TSS calculations
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="ftp">FTP (watts)</Label>
              <Input id="ftp" type="number" {...register('ftp')} />
              {errors.ftp && <p className="text-sm text-destructive">{errors.ftp.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="lthr">LTHR (bpm)</Label>
              <Input id="lthr" type="number" {...register('lthr')} />
              {errors.lthr && <p className="text-sm text-destructive">{errors.lthr.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="max_hr">Max HR (bpm)</Label>
              <div className="flex gap-2">
                <Input id="max_hr" type="number" {...register('max_hr')} />
                <Button type="button" variant="outline" onClick={handleDetectMaxHR} disabled={detectMaxHR.isPending}>
                  {detectMaxHR.isPending ? 'Detecting...' : 'Detect'}
                </Button>
              </div>
              {errors.max_hr && <p className="text-sm text-destructive">{errors.max_hr.message}</p>}
              {detectMaxHR.data && (
                <p className="text-sm text-muted-foreground">{detectMaxHR.data.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="resting_hr">Resting HR (bpm)</Label>
              <Input id="resting_hr" type="number" {...register('resting_hr')} />
              {errors.resting_hr && <p className="text-sm text-destructive">{errors.resting_hr.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="threshold_pace_minkm">Run Threshold Pace (min/km)</Label>
              <Controller
                name="threshold_pace_minkm"
                control={control}
                render={({ field }) => (
                  <PaceInput
                    id="threshold_pace_minkm"
                    value={field.value}
                    onChange={field.onChange}
                    onBlur={field.onBlur}
                  />
                )}
              />
              {errors.threshold_pace_minkm && <p className="text-sm text-destructive">{errors.threshold_pace_minkm.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="swim_threshold_pace">Swim Threshold Pace (min/100m)</Label>
              <Controller
                name="swim_threshold_pace"
                control={control}
                render={({ field }) => (
                  <PaceInput
                    id="swim_threshold_pace"
                    value={field.value}
                    onChange={field.onChange}
                    onBlur={field.onBlur}
                  />
                )}
              />
              {errors.swim_threshold_pace && <p className="text-sm text-destructive">{errors.swim_threshold_pace.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="weight_kg">Weight (kg)</Label>
              <Input id="weight_kg" type="number" step="0.1" {...register('weight_kg')} />
              {errors.weight_kg && <p className="text-sm text-destructive">{errors.weight_kg.message}</p>}
            </div>
          </div>

          <div className="flex items-center gap-4 pt-4">
            <Button type="submit" disabled={!isDirty || updateProfile.isPending || isRecalculating}>
              {updateProfile.isPending ? 'Saving...' : 'Save Thresholds'}
            </Button>
            {(profile?.metrics_dirty || isRecalculating) && !isRecalculating && (
              <Button type="button" variant="outline" onClick={handleRecalculate}>
                Recalculate Metrics
              </Button>
            )}
            {isRecalculating && (
              <Button type="button" variant="outline" onClick={cancelRecalculate}>
                Cancel
              </Button>
            )}
          </div>

          {isRecalculating && (
            <div className="space-y-2 pt-4">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">
                  {phase === 'activities' ? 'Processing activities...' : 'Calculating daily metrics...'}
                </span>
                <span className="text-muted-foreground">
                  {progress} / {total}
                </span>
              </div>
              <Progress value={total > 0 ? (progress / total) * 100 : 0} />
              {currentItem && (
                <p className="text-xs text-muted-foreground truncate">
                  {currentItem}
                </p>
              )}
              <p className="text-xs text-muted-foreground">
                Activities: {activitiesProcessed} / {totalActivities} | Days: {daysProcessed} / {totalDays}
              </p>
            </div>
          )}

          {updateProfile.isSuccess && <p className="text-sm text-green-600">Profile saved successfully!</p>}
        </form>
      </CardContent>
    </Card>
  )
}
