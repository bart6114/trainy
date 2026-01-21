import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getWellnessSettings,
  updateWellnessSettings,
  getMorningCheckin,
  submitMorningCheckin,
  getPendingFeedback,
  getActivityFeedback,
  submitActivityFeedback,
} from '@/api/wellness'
import type {
  UserSettingsUpdate,
  MorningCheckinRequest,
  ActivityFeedbackRequest,
} from '@/types'

// Settings
export function useWellnessSettings() {
  return useQuery({
    queryKey: ['wellness', 'settings'],
    queryFn: getWellnessSettings,
  })
}

export function useUpdateWellnessSettings() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: UserSettingsUpdate) => updateWellnessSettings(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wellness', 'settings'] })
      queryClient.invalidateQueries({ queryKey: ['wellness', 'pending'] })
    },
  })
}

// Morning Check-in
export function useMorningCheckin(date: string) {
  return useQuery({
    queryKey: ['wellness', 'morning-checkin', date],
    queryFn: () => getMorningCheckin(date),
  })
}

export function useSubmitMorningCheckin() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: MorningCheckinRequest) => submitMorningCheckin(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['wellness', 'morning-checkin', data.checkin_date] })
      queryClient.invalidateQueries({ queryKey: ['wellness', 'pending'] })
    },
  })
}

// Pending Feedback
export function usePendingFeedback() {
  return useQuery({
    queryKey: ['wellness', 'pending'],
    queryFn: getPendingFeedback,
    refetchInterval: 60000, // Refetch every minute
  })
}

// Activity Feedback
export function useActivityFeedback(activityId: number) {
  return useQuery({
    queryKey: ['wellness', 'activity-feedback', activityId],
    queryFn: () => getActivityFeedback(activityId),
    enabled: activityId > 0,
  })
}

export function useSubmitActivityFeedback() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ activityId, data }: { activityId: number; data: ActivityFeedbackRequest }) =>
      submitActivityFeedback(activityId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['wellness', 'activity-feedback', variables.activityId] })
      queryClient.invalidateQueries({ queryKey: ['wellness', 'pending'] })
    },
  })
}
