import { useState, useCallback, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { createRecalculateStream } from '@/api/metrics'
import type { RecalculateCompleteData } from '@/types'

interface RecalculateState {
  isRunning: boolean
  progress: number
  total: number
  phase: 'activities' | 'daily' | null
  currentItem: string | null
  activitiesProcessed: number
  daysProcessed: number
  totalActivities: number
  totalDays: number
}

export function useRecalculate() {
  const queryClient = useQueryClient()
  const eventSourceRef = useRef<EventSource | null>(null)
  const [state, setState] = useState<RecalculateState>({
    isRunning: false,
    progress: 0,
    total: 0,
    phase: null,
    currentItem: null,
    activitiesProcessed: 0,
    daysProcessed: 0,
    totalActivities: 0,
    totalDays: 0,
  })

  const startRecalculate = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }

    setState({
      isRunning: true,
      progress: 0,
      total: 0,
      phase: null,
      currentItem: null,
      activitiesProcessed: 0,
      daysProcessed: 0,
      totalActivities: 0,
      totalDays: 0,
    })

    const eventSource = createRecalculateStream()
    eventSourceRef.current = eventSource

    eventSource.addEventListener('start', (event) => {
      const data = JSON.parse(event.data)
      setState((prev) => ({
        ...prev,
        totalActivities: data.total_activities,
        totalDays: data.total_days,
      }))
    })

    eventSource.addEventListener('activity', (event) => {
      const data = JSON.parse(event.data)
      setState((prev) => ({
        ...prev,
        phase: 'activities',
        progress: data.progress,
        total: data.total,
        activitiesProcessed: data.progress,
        currentItem: data.activity_type ? `${data.activity_type} (${data.date || 'unknown date'})` : null,
      }))
    })

    eventSource.addEventListener('daily', (event) => {
      const data = JSON.parse(event.data)
      setState((prev) => ({
        ...prev,
        phase: 'daily',
        progress: data.progress,
        total: data.total,
        daysProcessed: data.progress,
        currentItem: data.date,
      }))
    })

    eventSource.addEventListener('complete', (event) => {
      const data: RecalculateCompleteData = JSON.parse(event.data)
      setState((prev) => ({
        ...prev,
        isRunning: false,
        activitiesProcessed: data.activities_processed,
        daysProcessed: data.days_processed,
        currentItem: null,
      }))
      eventSource.close()
      eventSourceRef.current = null

      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['metrics'] })
      queryClient.invalidateQueries({ queryKey: ['activities'] })
      queryClient.invalidateQueries({ queryKey: ['profile'] })
    })

    eventSource.onerror = () => {
      setState((prev) => ({
        ...prev,
        isRunning: false,
      }))
      eventSource.close()
      eventSourceRef.current = null
    }
  }, [queryClient])

  const cancelRecalculate = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
      setState((prev) => ({ ...prev, isRunning: false }))
    }
  }, [])

  return {
    ...state,
    startRecalculate,
    cancelRecalculate,
  }
}
