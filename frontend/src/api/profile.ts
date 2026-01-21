import { get, put, post } from './client'
import type { Profile, ProfileUpdate, MaxHRDetection } from '@/types'

export async function getProfile(): Promise<Profile> {
  return get<Profile>('/profile')
}

export async function updateProfile(data: ProfileUpdate): Promise<Profile> {
  return put<Profile, ProfileUpdate>('/profile', data)
}

export async function detectMaxHR(): Promise<MaxHRDetection> {
  return post<MaxHRDetection>('/profile/detect-max-hr')
}
