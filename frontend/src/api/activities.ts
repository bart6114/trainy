import { get } from './client'
import type { Activity, ActivityWithMetrics, PaginatedResponse } from '@/types'

export async function getActivities(
  offset = 0,
  limit = 50
): Promise<PaginatedResponse<Activity>> {
  return get<PaginatedResponse<Activity>>(`/activities?offset=${offset}&limit=${limit}`)
}

export async function getActivity(id: number): Promise<ActivityWithMetrics> {
  return get<ActivityWithMetrics>(`/activities/${id}`)
}
