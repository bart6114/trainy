import { get, post } from './client'
import type { CurrentMetrics, DailyMetrics, WeeklyTSS, SuccessResponse } from '@/types'

export async function getCurrentMetrics(): Promise<CurrentMetrics> {
  return get<CurrentMetrics>('/metrics/current')
}

export async function getDailyMetrics(
  start?: string,
  end?: string
): Promise<DailyMetrics> {
  const params = new URLSearchParams()
  if (start) params.set('start', start)
  if (end) params.set('end', end)
  const query = params.toString()
  return get<DailyMetrics>(`/metrics/daily${query ? `?${query}` : ''}`)
}

export async function getWeeklyTSS(weeks = 12): Promise<WeeklyTSS> {
  return get<WeeklyTSS>(`/metrics/weekly?weeks=${weeks}`)
}

export async function recalculateMetrics(): Promise<SuccessResponse> {
  return post<SuccessResponse>('/metrics/recalculate')
}

export function createRecalculateStream(): EventSource {
  return new EventSource('/api/v1/metrics/recalculate/stream')
}
