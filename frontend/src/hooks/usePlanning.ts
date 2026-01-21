import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  generateWorkouts,
  getUpcomingWorkouts,
  getWorkoutsForDate,
  deleteWorkout,
  skipWorkout,
} from '@/api/planning'

export function useUpcomingWorkouts(days: number = 7) {
  return useQuery({
    queryKey: ['planned-workouts', 'upcoming', days],
    queryFn: () => getUpcomingWorkouts(days),
  })
}

export function useDateWorkouts(date: string) {
  return useQuery({
    queryKey: ['planned-workouts', 'date', date],
    queryFn: () => getWorkoutsForDate(date),
    enabled: !!date,
  })
}

export function useGenerateWorkouts() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (prompt: string) => generateWorkouts(prompt),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['planned-workouts'] })
      queryClient.invalidateQueries({ queryKey: ['calendar'] })
    },
  })
}

export function useDeleteWorkout() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => deleteWorkout(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['planned-workouts'] })
      queryClient.invalidateQueries({ queryKey: ['calendar'] })
    },
  })
}

export function useSkipWorkout() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => skipWorkout(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['planned-workouts'] })
      queryClient.invalidateQueries({ queryKey: ['calendar'] })
    },
  })
}
