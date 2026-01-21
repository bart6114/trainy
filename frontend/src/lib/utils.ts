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
