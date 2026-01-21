import { get, post } from './client'
import type {
  PowerCurveResponse,
  InjuryAnalysisResponse,
  PainLocationCount,
  MergePainLocationsRequest,
  MergePainLocationsResponse,
} from '@/types'

export async function getPowerCurve(days = 90): Promise<PowerCurveResponse> {
  return get<PowerCurveResponse>(`/analytics/power-curve?days=${days}`)
}

export async function getInjuryAnalysis(days = 90): Promise<InjuryAnalysisResponse> {
  return get<InjuryAnalysisResponse>(`/analytics/injury-analysis?days=${days}`)
}

export async function getPainLocations(): Promise<PainLocationCount[]> {
  return get<PainLocationCount[]>('/analytics/pain-locations')
}

export async function mergePainLocations(
  request: MergePainLocationsRequest
): Promise<MergePainLocationsResponse> {
  return post<MergePainLocationsResponse>('/analytics/merge-pain-locations', request)
}
