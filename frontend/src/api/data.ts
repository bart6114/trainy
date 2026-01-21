import { get, del } from './client'
import type { DataStats, DeleteResponse } from '@/types'

export async function getDataStats(): Promise<DataStats> {
  return get<DataStats>('/data/stats')
}

export async function deleteAllData(): Promise<DeleteResponse> {
  return del<DeleteResponse>('/data/all')
}

export async function deleteAllActivities(): Promise<DeleteResponse> {
  return del<DeleteResponse>('/data/activities')
}

export async function deleteAllPlannedWorkouts(): Promise<DeleteResponse> {
  return del<DeleteResponse>('/data/planned-workouts')
}
