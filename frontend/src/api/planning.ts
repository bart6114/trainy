import { get, post, del, patch } from './client'
import type {
  GeneratedWorkoutsResponse,
  UpcomingWorkoutsResponse,
  DateWorkoutsResponse,
  SuccessResponse,
  AcceptProposalRequest,
  ProposedWorkout,
} from '@/types'

export async function getUpcomingWorkouts(days: number = 7): Promise<UpcomingWorkoutsResponse> {
  return get<UpcomingWorkoutsResponse>(`/planned-workouts/upcoming?days=${days}`)
}

export async function getWorkoutsForDate(date: string): Promise<DateWorkoutsResponse> {
  return get<DateWorkoutsResponse>(`/planned-workouts/date/${date}`)
}

export async function deleteWorkout(id: number): Promise<SuccessResponse> {
  return del<SuccessResponse>(`/planned-workouts/${id}`)
}

export async function skipWorkout(id: number): Promise<SuccessResponse> {
  return patch<SuccessResponse>(`/planned-workouts/${id}/skip`)
}

export async function acceptProposal(workouts: ProposedWorkout[]): Promise<GeneratedWorkoutsResponse> {
  return post<GeneratedWorkoutsResponse, AcceptProposalRequest>('/planned-workouts/accept', {
    workouts,
  })
}
