import { useQuery } from '@tanstack/react-query'
import { getActivities, getActivity, getActivityTrack } from '@/api/activities'

export function useActivities(offset = 0, limit = 50) {
  return useQuery({
    queryKey: ['activities', offset, limit],
    queryFn: () => getActivities(offset, limit),
  })
}

export function useActivity(id: number) {
  return useQuery({
    queryKey: ['activity', id],
    queryFn: () => getActivity(id),
    enabled: !!id,
  })
}

export function useActivityTrack(id: number, enabled = true) {
  return useQuery({
    queryKey: ['activity-track', id],
    queryFn: () => getActivityTrack(id),
    enabled: !!id && enabled,
  })
}
