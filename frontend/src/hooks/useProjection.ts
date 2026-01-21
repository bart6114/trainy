import { useMemo } from 'react'
import { useUpcomingWorkouts } from './usePlanning'
import { calculateProjection } from '@/lib/projection'
import type { ProjectedDataPoint } from '@/types'

interface LatestMetrics {
  ctl: number
  atl: number
}

interface UseFormProjectionResult {
  projectedData: ProjectedDataPoint[]
  isLoading: boolean
}

export function useFormProjection(
  enabled: boolean,
  latestMetrics: LatestMetrics | null,
  days: number = 42
): UseFormProjectionResult {
  const { data: workoutsResponse, isLoading } = useUpcomingWorkouts(days)

  const projectedData = useMemo(() => {
    if (!enabled || !latestMetrics || !workoutsResponse) {
      return []
    }

    return calculateProjection(latestMetrics, workoutsResponse.workouts, days)
  }, [enabled, latestMetrics, workoutsResponse, days])

  return {
    projectedData,
    isLoading: enabled && isLoading,
  }
}
