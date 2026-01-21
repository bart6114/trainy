import { get } from './client'
import type { ImportStatus } from '@/types'

export async function getImportStatus(): Promise<ImportStatus> {
  return get<ImportStatus>('/import/status')
}

export function createImportStream(
  fromDate?: string
): EventSource {
  const params = new URLSearchParams()
  if (fromDate) params.set('from_date', fromDate)
  const query = params.toString()
  return new EventSource(`/api/v1/import/stream${query ? `?${query}` : ''}`)
}
