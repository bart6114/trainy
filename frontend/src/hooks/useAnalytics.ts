import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getPowerCurve, getInjuryAnalysis, getPainLocations, mergePainLocations } from '@/api/analytics'
import type { MergePainLocationsRequest } from '@/types'

export function usePowerCurve(days = 90) {
  return useQuery({
    queryKey: ['analytics', 'power-curve', days],
    queryFn: () => getPowerCurve(days),
  })
}

export function useInjuryAnalysis(days = 90) {
  return useQuery({
    queryKey: ['analytics', 'injury-analysis', days],
    queryFn: () => getInjuryAnalysis(days),
  })
}

export function usePainLocations() {
  return useQuery({
    queryKey: ['analytics', 'pain-locations'],
    queryFn: () => getPainLocations(),
  })
}

export function useMergePainLocations() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (request: MergePainLocationsRequest) => mergePainLocations(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analytics', 'injury-analysis'] })
      queryClient.invalidateQueries({ queryKey: ['analytics', 'pain-locations'] })
    },
  })
}
