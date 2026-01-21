import { useState, useCallback, useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getImportStatus, createImportStream } from '@/api/import'
import type { ImportCompleteData } from '@/types'

export function useImportStatus() {
  return useQuery({
    queryKey: ['import', 'status'],
    queryFn: getImportStatus,
  })
}

interface ImportState {
  isRunning: boolean
  progress: number
  total: number
  imported: number
  skipped: number
  errors: number
  currentFile: string | null
  lastError: string | null
}

export function useImport() {
  const queryClient = useQueryClient()
  const eventSourceRef = useRef<EventSource | null>(null)
  const [state, setState] = useState<ImportState>({
    isRunning: false,
    progress: 0,
    total: 0,
    imported: 0,
    skipped: 0,
    errors: 0,
    currentFile: null,
    lastError: null,
  })

  const startImport = useCallback((fromDate?: string) => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }

    setState({
      isRunning: true,
      progress: 0,
      total: 0,
      imported: 0,
      skipped: 0,
      errors: 0,
      currentFile: null,
      lastError: null,
    })

    const eventSource = createImportStream(fromDate)
    eventSourceRef.current = eventSource

    eventSource.addEventListener('start', (event) => {
      const data = JSON.parse(event.data)
      setState((prev) => ({ ...prev, total: data.total }))
    })

    eventSource.addEventListener('import', (event) => {
      const data = JSON.parse(event.data)
      setState((prev) => ({
        ...prev,
        progress: data.progress,
        imported: prev.imported + 1,
        currentFile: data.file,
      }))
    })

    eventSource.addEventListener('skip', (event) => {
      const data = JSON.parse(event.data)
      setState((prev) => ({
        ...prev,
        progress: data.progress,
        skipped: prev.skipped + 1,
        currentFile: data.file,
      }))
    })

    eventSource.addEventListener('error', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data)
        setState((prev) => ({
          ...prev,
          errors: prev.errors + 1,
          lastError: `${data.file}: ${data.error}`,
        }))
      } catch {
        // Connection error, not a data event
      }
    })

    eventSource.addEventListener('complete', (event) => {
      const data: ImportCompleteData = JSON.parse(event.data)
      setState((prev) => ({
        ...prev,
        isRunning: false,
        imported: data.imported,
        skipped: data.skipped,
        errors: data.errors,
        progress: data.total,
        total: data.total,
        currentFile: null,
      }))
      eventSource.close()
      eventSourceRef.current = null

      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['activities'] })
      queryClient.invalidateQueries({ queryKey: ['metrics'] })
      queryClient.invalidateQueries({ queryKey: ['calendar'] })
      queryClient.invalidateQueries({ queryKey: ['import', 'status'] })
    })

    eventSource.onerror = () => {
      setState((prev) => ({
        ...prev,
        isRunning: false,
        lastError: 'Connection lost',
      }))
      eventSource.close()
      eventSourceRef.current = null
    }
  }, [queryClient])

  const cancelImport = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
      setState((prev) => ({ ...prev, isRunning: false }))
    }
  }, [])

  return {
    ...state,
    startImport,
    cancelImport,
  }
}
