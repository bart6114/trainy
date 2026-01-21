import { addDays, format } from 'date-fns'
import type { PlannedWorkout, ProjectedDataPoint } from '@/types'

interface LatestMetrics {
  ctl: number
  atl: number
}

/**
 * Estimate TSS from duration when target_tss is not available.
 * Uses moderate intensity factor (0.7) as default.
 */
function estimateTss(durationSeconds: number | null): number {
  if (!durationSeconds) return 0
  const durationHours = durationSeconds / 3600
  const intensityFactor = 0.7
  return durationHours * Math.pow(intensityFactor, 2) * 100
}

// EWMA decay factors using true exponential formula: 1 - e^(-1/k)
// Reference: TrainingPeaks Performance Manager (Coggan/Allen)
// https://www.trainingpeaks.com/learn/articles/the-science-of-the-performance-manager/
const CTL_DECAY = 1 - Math.exp(-1 / 42) // ≈ 0.02353 (42-day time constant)
const ATL_DECAY = 1 - Math.exp(-1 / 7) // ≈ 0.13314 (7-day time constant)

/**
 * Calculate projected CTL/ATL/TSB for upcoming days based on planned workouts.
 *
 * Uses EWMA with true exponential decay (matching backend):
 *   CTL_today = CTL_yesterday + (TSS_today - CTL_yesterday) * (1 - e^(-1/42))
 *   ATL_today = ATL_yesterday + (TSS_today - ATL_yesterday) * (1 - e^(-1/7))
 *   TSB = CTL - ATL
 *
 * References:
 * - TrainingPeaks Performance Manager: https://www.trainingpeaks.com/learn/articles/the-science-of-the-performance-manager/
 * - Coggan/Allen power training formulas
 */
export function calculateProjection(
  latestMetrics: LatestMetrics,
  plannedWorkouts: PlannedWorkout[],
  days: number
): ProjectedDataPoint[] {
  const result: ProjectedDataPoint[] = []

  // Group workouts by date for quick lookup
  const workoutsByDate = new Map<string, PlannedWorkout[]>()
  for (const workout of plannedWorkouts) {
    const date = workout.planned_date
    if (!workoutsByDate.has(date)) {
      workoutsByDate.set(date, [])
    }
    workoutsByDate.get(date)!.push(workout)
  }

  let ctl = latestMetrics.ctl
  let atl = latestMetrics.atl

  const startDate = new Date()

  for (let i = 1; i <= days; i++) {
    const date = format(addDays(startDate, i), 'yyyy-MM-dd')
    const dayWorkouts = workoutsByDate.get(date) || []

    // Calculate total TSS for the day
    let plannedTss = 0
    for (const workout of dayWorkouts) {
      if (workout.target_tss != null) {
        plannedTss += workout.target_tss
      } else {
        plannedTss += estimateTss(workout.target_duration_s)
      }
    }

    // Apply EWMA formulas with true exponential decay
    ctl = ctl + (plannedTss - ctl) * CTL_DECAY
    atl = atl + (plannedTss - atl) * ATL_DECAY
    const tsb = ctl - atl

    result.push({
      date,
      ctlProjected: ctl,
      atlProjected: atl,
      tsbProjected: tsb,
      plannedTss,
      isRestDay: dayWorkouts.length === 0,
    })
  }

  return result
}
