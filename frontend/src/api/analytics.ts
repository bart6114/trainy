import { get } from './client'
import type { PowerCurveResponse } from '@/types'

export async function getPowerCurve(days = 90): Promise<PowerCurveResponse> {
  return get<PowerCurveResponse>(`/analytics/power-curve?days=${days}`)
}
