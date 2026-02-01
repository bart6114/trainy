import { get } from './client'
import type { Activity, ActivityWithMetrics, ActivityTrackResponse, ActivityStreams, PaginatedResponse } from '@/types'

export async function getActivities(
  offset = 0,
  limit = 50
): Promise<PaginatedResponse<Activity>> {
  return get<PaginatedResponse<Activity>>(`/activities?offset=${offset}&limit=${limit}`)
}

export async function getActivity(id: number): Promise<ActivityWithMetrics> {
  return get<ActivityWithMetrics>(`/activities/${id}`)
}

export async function getActivityTrack(id: number): Promise<ActivityTrackResponse> {
  return get<ActivityTrackResponse>(`/activities/${id}/track`)
}

export async function getActivityStreams(id: number): Promise<ActivityStreams> {
  return get<ActivityStreams>(`/activities/${id}/streams`)
}
