import { get } from './client'
import type { CalendarMonth, CalendarDate } from '@/types'

export async function getCalendarMonth(
  year: number,
  month: number
): Promise<CalendarMonth> {
  return get<CalendarMonth>(`/calendar/${year}/${month}`)
}

export async function getCalendarDate(date: string): Promise<CalendarDate> {
  return get<CalendarDate>(`/calendar/date/${date}`)
}
