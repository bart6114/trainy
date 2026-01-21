import { get, put, post } from './client'
import type {
  UserSettings,
  UserSettingsUpdate,
  MorningCheckin,
  MorningCheckinRequest,
  PendingFeedback,
  ActivityFeedback,
  ActivityFeedbackRequest,
} from '@/types'

// Settings
export async function getWellnessSettings(): Promise<UserSettings> {
  return get<UserSettings>('/wellness/settings')
}

export async function updateWellnessSettings(data: UserSettingsUpdate): Promise<UserSettings> {
  return put<UserSettings, UserSettingsUpdate>('/wellness/settings', data)
}

// Morning Check-in
export async function getMorningCheckin(date: string): Promise<MorningCheckin | null> {
  return get<MorningCheckin | null>(`/wellness/morning-checkin/${date}`)
}

export async function submitMorningCheckin(data: MorningCheckinRequest): Promise<MorningCheckin> {
  return post<MorningCheckin, MorningCheckinRequest>('/wellness/morning-checkin', data)
}

// Pending Feedback
export async function getPendingFeedback(): Promise<PendingFeedback> {
  return get<PendingFeedback>('/wellness/pending-feedback')
}

// Activity Feedback
export async function getActivityFeedback(activityId: number): Promise<ActivityFeedback | null> {
  return get<ActivityFeedback | null>(`/wellness/activity-feedback/${activityId}`)
}

export async function submitActivityFeedback(
  activityId: number,
  data: ActivityFeedbackRequest
): Promise<ActivityFeedback> {
  return post<ActivityFeedback, ActivityFeedbackRequest>(
    `/wellness/activity-feedback/${activityId}`,
    data
  )
}
