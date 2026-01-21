import { useQuery } from '@tanstack/react-query'
import { getCalendarMonth, getCalendarDate } from '@/api/calendar'

export function useCalendarMonth(year: number, month: number) {
  return useQuery({
    queryKey: ['calendar', year, month],
    queryFn: () => getCalendarMonth(year, month),
  })
}

export function useCalendarDate(date: string) {
  return useQuery({
    queryKey: ['calendar', 'date', date],
    queryFn: () => getCalendarDate(date),
    enabled: !!date,
  })
}
