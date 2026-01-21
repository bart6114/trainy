import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDuration(seconds: number | null | undefined): string {
  if (!seconds) return '0m'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) {
    return `${hours}h ${minutes}m`
  }
  return `${minutes}m`
}

export function formatDistance(meters: number | null | undefined): string {
  if (!meters) return '0 km'
  const km = meters / 1000
  return `${km.toFixed(1)} km`
}

export function formatPace(mps: number | null | undefined): string {
  if (!mps || mps === 0) return '-'
  const minPerKm = 1000 / 60 / mps
  const mins = Math.floor(minPerKm)
  const secs = Math.round((minPerKm - mins) * 60)
  return `${mins}:${secs.toString().padStart(2, '0')} /km`
}

export function formatSpeed(mps: number | null | undefined): string {
  if (!mps || mps === 0) return '-'
  const kmh = mps * 3.6
  return `${kmh.toFixed(1)} km/h`
}

export function isCyclingActivity(activityType: string): boolean {
  const cyclingTypes = ['cycling', 'cycle', 'bike', 'biking', 'virtual_ride', 'road_cycling', 'mountain_biking', 'gravel_cycling']
  return cyclingTypes.includes(activityType.toLowerCase())
}

export function getFormStatusColor(status: string): string {
  switch (status) {
    case 'Fresh':
      return 'text-green-600 bg-green-100'
    case 'Neutral':
      return 'text-blue-600 bg-blue-100'
    case 'Tired':
      return 'text-orange-600 bg-orange-100'
    case 'Exhausted':
      return 'text-red-600 bg-red-100'
    case 'Transition':
      return 'text-yellow-600 bg-yellow-100'
    default:
      return 'text-gray-600 bg-gray-100'
  }
}

export function getACWRStatusColor(status: string): string {
  switch (status) {
    case 'Optimal':
      return 'text-green-600 bg-green-100'
    case 'Undertrained':
      return 'text-yellow-600 bg-yellow-100'
    case 'Caution':
      return 'text-orange-600 bg-orange-100'
    case 'Danger':
      return 'text-red-600 bg-red-100'
    default:
      return 'text-gray-600 bg-gray-100'
  }
}

export function getActivityIcon(type: string): string {
  switch (type.toLowerCase()) {
    case 'run':
    case 'running':
      return 'running'
    case 'cycle':
    case 'cycling':
      return 'bike'
    case 'swim':
    case 'swimming':
      return 'waves'
    case 'strength':
    case 'weight_training':
      return 'dumbbell'
    default:
      return 'activity'
  }
}

// Workout intensity types and helpers
export type WorkoutIntensity = 'low' | 'medium' | 'medium-high' | 'high'

export const intensityBarColors: Record<WorkoutIntensity, string> = {
  low: 'bg-emerald-400/70 dark:bg-emerald-500/50',
  medium: 'bg-amber-400/80 dark:bg-amber-500/60',
  'medium-high': 'bg-orange-400/85 dark:bg-orange-500/65',
  high: 'bg-red-400/90 dark:bg-red-500/70',
}

const workoutTypeIntensityMap: Record<string, WorkoutIntensity> = {
  // Low intensity
  easy: 'low',
  recovery: 'low',
  // Medium intensity
  tempo: 'medium',
  endurance: 'medium',
  base: 'medium',
  // Medium-high intensity
  long: 'medium-high',
  threshold: 'medium-high',
  // High intensity
  intervals: 'high',
  vo2max: 'high',
  race: 'high',
  hiit: 'high',
}

export function getWorkoutIntensity(workoutType: string | null | undefined): WorkoutIntensity | null {
  if (!workoutType) return null
  return workoutTypeIntensityMap[workoutType.toLowerCase()] || null
}

export function getIntensityFromTSS(tss: number | null | undefined): WorkoutIntensity | null {
  if (tss === null || tss === undefined) return null
  if (tss < 50) return 'low'
  if (tss < 80) return 'medium'
  if (tss < 120) return 'medium-high'
  return 'high'
}

const intensityOrder: Record<WorkoutIntensity, number> = {
  low: 1,
  medium: 2,
  'medium-high': 3,
  high: 4,
}

export function getDayMaxIntensity(
  plannedWorkouts: Array<{ workout_type: string | null; target_tss: number | null; status: string }>,
  activities: Array<{ tss: number | null }>
): WorkoutIntensity | null {
  let maxIntensity: WorkoutIntensity | null = null

  // Check planned workouts (only those still planned)
  for (const workout of plannedWorkouts) {
    if (workout.status !== 'planned') continue
    const intensity = getWorkoutIntensity(workout.workout_type) || getIntensityFromTSS(workout.target_tss)
    if (intensity && (!maxIntensity || intensityOrder[intensity] > intensityOrder[maxIntensity])) {
      maxIntensity = intensity
    }
  }

  // Check completed activities
  for (const activity of activities) {
    const intensity = getIntensityFromTSS(activity.tss)
    if (intensity && (!maxIntensity || intensityOrder[intensity] > intensityOrder[maxIntensity])) {
      maxIntensity = intensity
    }
  }

  return maxIntensity
}
