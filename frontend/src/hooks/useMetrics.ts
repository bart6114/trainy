import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getCurrentMetrics, getDailyMetrics, getWeeklyTSS, recalculateMetrics } from '@/api/metrics'

export function useCurrentMetrics() {
  return useQuery({
    queryKey: ['metrics', 'current'],
    queryFn: getCurrentMetrics,
  })
}

export function useDailyMetrics(start?: string, end?: string) {
  return useQuery({
    queryKey: ['metrics', 'daily', start, end],
    queryFn: () => getDailyMetrics(start, end),
  })
}

export function useWeeklyTSS(weeks = 12) {
  return useQuery({
    queryKey: ['metrics', 'weekly', weeks],
    queryFn: () => getWeeklyTSS(weeks),
  })
}

export function useRecalculateMetrics() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: recalculateMetrics,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['metrics'] })
    },
  })
}
