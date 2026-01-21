import { useQuery } from '@tanstack/react-query'
import { getPowerCurve } from '@/api/analytics'

export function usePowerCurve(days = 90) {
  return useQuery({
    queryKey: ['analytics', 'power-curve', days],
    queryFn: () => getPowerCurve(days),
  })
}
