import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getDataStats,
  deleteAllData,
  deleteAllActivities,
  deleteAllPlannedWorkouts,
} from '@/api/data'

export function useDataStats() {
  return useQuery({
    queryKey: ['dataStats'],
    queryFn: getDataStats,
  })
}

export function useDeleteAllData() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: deleteAllData,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataStats'] })
      queryClient.invalidateQueries({ queryKey: ['activities'] })
      queryClient.invalidateQueries({ queryKey: ['calendar'] })
      queryClient.invalidateQueries({ queryKey: ['metrics'] })
      queryClient.invalidateQueries({ queryKey: ['plannedWorkouts'] })
    },
  })
}

export function useDeleteAllActivities() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: deleteAllActivities,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataStats'] })
      queryClient.invalidateQueries({ queryKey: ['activities'] })
      queryClient.invalidateQueries({ queryKey: ['calendar'] })
      queryClient.invalidateQueries({ queryKey: ['metrics'] })
    },
  })
}

export function useDeleteAllPlannedWorkouts() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: deleteAllPlannedWorkouts,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataStats'] })
      queryClient.invalidateQueries({ queryKey: ['calendar'] })
      queryClient.invalidateQueries({ queryKey: ['plannedWorkouts'] })
    },
  })
}
