import { useState, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import type {
  CoachingMessage,
  CoachingProposal,
  ToolCallInfo,
  ToolResultInfo,
  CoachingThinkingEvent,
  CoachingToolCallEvent,
  CoachingToolResultEvent,
  CoachingTextEvent,
  CoachingProposalEvent,
  AcceptCoachingProposalResponse,
} from '@/types'

const API_BASE = '/api/v1'

interface CoachingChatState {
  isProcessing: boolean
  thinkingMessage: string | null
  activeToolCall: ToolCallInfo | null
  conversation: CoachingMessage[]
  proposal: CoachingProposal | null
  error: string | null
}

// Track tool calls and results for the current assistant message
interface PendingAssistantMessage {
  toolCalls: ToolCallInfo[]
  toolResults: ToolResultInfo[]
  textContent: string
}

export function useCoachingChat() {
  const queryClient = useQueryClient()
  const [state, setState] = useState<CoachingChatState>({
    isProcessing: false,
    thinkingMessage: null,
    activeToolCall: null,
    conversation: [],
    proposal: null,
    error: null,
  })

  const processSSEStream = useCallback(
    async (
      response: Response,
      userMessage: string,
      onComplete: () => void
    ) => {
      const reader = response.body?.getReader()
      if (!reader) {
        setState((prev) => ({
          ...prev,
          isProcessing: false,
          error: 'Failed to read response stream',
        }))
        return
      }

      const decoder = new TextDecoder()
      let buffer = ''

      // Accumulate data for the assistant message
      const pending: PendingAssistantMessage = {
        toolCalls: [],
        toolResults: [],
        textContent: '',
      }

      try {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })

          // Process complete SSE events
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          let currentEvent = ''
          let currentData = ''

          for (const line of lines) {
            if (line.startsWith('event: ')) {
              currentEvent = line.slice(7)
            } else if (line.startsWith('data: ')) {
              currentData = line.slice(6)

              if (currentEvent && currentData) {
                try {
                  const data = JSON.parse(currentData)

                  switch (currentEvent) {
                    case 'thinking': {
                      const thinking = data as CoachingThinkingEvent
                      setState((prev) => ({
                        ...prev,
                        thinkingMessage: thinking.message,
                        activeToolCall: null,
                      }))
                      break
                    }
                    case 'tool_call': {
                      const toolCall = data as CoachingToolCallEvent
                      const callInfo: ToolCallInfo = {
                        tool_name: toolCall.tool_name,
                        arguments: toolCall.arguments,
                      }
                      pending.toolCalls.push(callInfo)
                      setState((prev) => ({
                        ...prev,
                        thinkingMessage: null,
                        activeToolCall: callInfo,
                      }))
                      break
                    }
                    case 'tool_result': {
                      const result = data as CoachingToolResultEvent
                      pending.toolResults.push({
                        tool_name: result.tool_name,
                        result: result.result,
                        summary: result.summary,
                      })
                      setState((prev) => ({
                        ...prev,
                        activeToolCall: null,
                      }))
                      break
                    }
                    case 'text': {
                      const text = data as CoachingTextEvent
                      pending.textContent = text.content
                      break
                    }
                    case 'proposal': {
                      const proposal = data as CoachingProposalEvent
                      setState((prev) => ({
                        ...prev,
                        proposal: {
                          proposal_id: proposal.proposal_id,
                          workouts: proposal.workouts,
                          deletions: proposal.deletions || [],
                        },
                      }))
                      break
                    }
                    case 'error': {
                      setState((prev) => ({
                        ...prev,
                        isProcessing: false,
                        thinkingMessage: null,
                        activeToolCall: null,
                        error: data.message,
                      }))
                      return
                    }
                  }
                } catch (e) {
                  console.error('Failed to parse SSE data:', e)
                }

                currentEvent = ''
                currentData = ''
              }
            }
          }
        }

        // Stream complete - finalize the assistant message
        const assistantMessage: CoachingMessage = {
          role: 'assistant',
          content: pending.textContent,
          toolCalls: pending.toolCalls.length > 0 ? pending.toolCalls : undefined,
          toolResults: pending.toolResults.length > 0 ? pending.toolResults : undefined,
        }

        // Add user message and assistant response to conversation
        const newUserMessage: CoachingMessage = {
          role: 'user',
          content: userMessage,
        }

        setState((prev) => ({
          ...prev,
          isProcessing: false,
          thinkingMessage: null,
          activeToolCall: null,
          conversation: [...prev.conversation, newUserMessage, assistantMessage],
        }))

        onComplete()
      } catch (e) {
        setState((prev) => ({
          ...prev,
          isProcessing: false,
          thinkingMessage: null,
          activeToolCall: null,
          error: e instanceof Error ? e.message : 'Stream processing error',
        }))
      } finally {
        reader.releaseLock()
      }
    },
    []
  )

  const sendMessage = useCallback(
    async (message: string) => {
      setState((prev) => ({
        ...prev,
        isProcessing: true,
        thinkingMessage: 'Thinking...',
        activeToolCall: null,
        error: null,
      }))

      try {
        // Build conversation history for the API (without tool details)
        const conversationHistory = state.conversation.map((msg) => ({
          role: msg.role,
          content: msg.content,
        }))

        const response = await fetch(`${API_BASE}/coaching/chat/stream`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message,
            conversation_history: conversationHistory,
          }),
        })

        if (!response.ok) {
          throw new Error(`HTTP error: ${response.status}`)
        }

        await processSSEStream(response, message, () => {})
      } catch (e) {
        setState((prev) => ({
          ...prev,
          isProcessing: false,
          thinkingMessage: null,
          activeToolCall: null,
          error: e instanceof Error ? e.message : 'An error occurred',
        }))
      }
    },
    [state.conversation, processSSEStream]
  )

  const acceptProposal = useCallback(async () => {
    if (!state.proposal) {
      setState((prev) => ({ ...prev, error: 'No proposal to accept' }))
      return
    }

    try {
      const response = await fetch(`${API_BASE}/coaching/accept-proposal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          proposal_id: state.proposal.proposal_id,
          workouts: state.proposal.workouts,
          deletions: state.proposal.deletions,
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`)
      }

      const result: AcceptCoachingProposalResponse = await response.json()

      // Invalidate queries to refresh workout lists
      queryClient.invalidateQueries({ queryKey: ['planned-workouts'] })
      queryClient.invalidateQueries({ queryKey: ['calendar'] })

      // Clear proposal after accepting
      setState((prev) => ({
        ...prev,
        proposal: null,
      }))

      return result
    } catch (e) {
      setState((prev) => ({
        ...prev,
        error: e instanceof Error ? e.message : 'Failed to save workouts',
      }))
    }
  }, [state.proposal, queryClient])

  const rejectProposal = useCallback(() => {
    setState((prev) => ({
      ...prev,
      proposal: null,
    }))
  }, [])

  const reset = useCallback(() => {
    setState({
      isProcessing: false,
      thinkingMessage: null,
      activeToolCall: null,
      conversation: [],
      proposal: null,
      error: null,
    })
  }, [])

  const clearError = useCallback(() => {
    setState((prev) => ({ ...prev, error: null }))
  }, [])

  return {
    ...state,
    sendMessage,
    acceptProposal,
    rejectProposal,
    reset,
    clearError,
  }
}
