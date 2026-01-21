import { useState, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { acceptProposal } from '@/api/planning'
import type {
  ConversationMessage,
  WorkoutProposal,
  ThinkingEvent,
  ProposalEvent,
  QuestionEvent,
} from '@/types'

const API_BASE = '/api/v1'

interface ConversationalPlanningState {
  isGenerating: boolean
  thinkingPhase: 'analyzing' | 'generating' | null
  thinkingMessage: string | null
  conversation: ConversationMessage[]
  proposal: WorkoutProposal | null
  pendingQuestion: QuestionEvent | null
  error: string | null
}

export function useConversationalPlanning() {
  const queryClient = useQueryClient()
  const [state, setState] = useState<ConversationalPlanningState>({
    isGenerating: false,
    thinkingPhase: null,
    thinkingMessage: null,
    conversation: [],
    proposal: null,
    pendingQuestion: null,
    error: null,
  })

  const processSSEStream = useCallback(
    async (
      response: Response,
      onThinking: (event: ThinkingEvent) => void,
      onProposal: (event: ProposalEvent) => void,
      onQuestion: (event: QuestionEvent) => void,
      onError: (message: string) => void
    ) => {
      const reader = response.body?.getReader()
      if (!reader) {
        onError('Failed to read response stream')
        return
      }

      const decoder = new TextDecoder()
      let buffer = ''

      try {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })

          // Process complete SSE events
          const lines = buffer.split('\n')
          buffer = lines.pop() || '' // Keep incomplete line in buffer

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
                    case 'thinking':
                      onThinking(data as ThinkingEvent)
                      break
                    case 'proposal':
                      onProposal(data as ProposalEvent)
                      break
                    case 'question':
                      onQuestion(data as QuestionEvent)
                      break
                    case 'error':
                      onError(data.message)
                      break
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
      } finally {
        reader.releaseLock()
      }
    },
    []
  )

  const generate = useCallback(
    async (prompt: string) => {
      setState((prev) => ({
        ...prev,
        isGenerating: true,
        thinkingPhase: null,
        thinkingMessage: null,
        pendingQuestion: null,
        error: null,
      }))

      // Add user message to conversation
      const userMessage: ConversationMessage = { role: 'user', content: prompt }

      try {
        const response = await fetch(`${API_BASE}/planned-workouts/generate/stream`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt,
            conversation_history: state.conversation,
          }),
        })

        if (!response.ok) {
          throw new Error(`HTTP error: ${response.status}`)
        }

        await processSSEStream(
          response,
          (thinking) => {
            setState((prev) => ({
              ...prev,
              thinkingPhase: thinking.phase,
              thinkingMessage: thinking.message,
            }))
          },
          (proposal) => {
            const assistantMessage: ConversationMessage = {
              role: 'assistant',
              content: proposal.assistant_message,
            }

            setState((prev) => ({
              ...prev,
              isGenerating: false,
              thinkingPhase: null,
              thinkingMessage: null,
              conversation: [...prev.conversation, userMessage, assistantMessage],
              proposal: {
                workouts: proposal.workouts,
                assistant_message: proposal.assistant_message,
              },
            }))
          },
          (question) => {
            // AI is asking a clarifying question
            const assistantMessage: ConversationMessage = {
              role: 'assistant',
              content: question.message,
            }

            setState((prev) => ({
              ...prev,
              isGenerating: false,
              thinkingPhase: null,
              thinkingMessage: null,
              conversation: [...prev.conversation, userMessage, assistantMessage],
              pendingQuestion: question,
            }))
          },
          (errorMessage) => {
            setState((prev) => ({
              ...prev,
              isGenerating: false,
              thinkingPhase: null,
              thinkingMessage: null,
              error: errorMessage,
            }))
          }
        )
      } catch (e) {
        setState((prev) => ({
          ...prev,
          isGenerating: false,
          thinkingPhase: null,
          thinkingMessage: null,
          error: e instanceof Error ? e.message : 'An error occurred',
        }))
      }
    },
    [state.conversation, processSSEStream]
  )

  const refine = useCallback(
    async (refinement: string) => {
      if (!state.proposal) {
        setState((prev) => ({ ...prev, error: 'No proposal to refine' }))
        return
      }

      setState((prev) => ({
        ...prev,
        isGenerating: true,
        thinkingPhase: null,
        thinkingMessage: null,
        pendingQuestion: null,
        error: null,
      }))

      const userMessage: ConversationMessage = { role: 'user', content: refinement }

      try {
        const response = await fetch(`${API_BASE}/planned-workouts/refine/stream`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            refinement,
            current_proposal: state.proposal.workouts,
            conversation_history: state.conversation,
          }),
        })

        if (!response.ok) {
          throw new Error(`HTTP error: ${response.status}`)
        }

        await processSSEStream(
          response,
          (thinking) => {
            setState((prev) => ({
              ...prev,
              thinkingPhase: thinking.phase,
              thinkingMessage: thinking.message,
            }))
          },
          (proposal) => {
            const assistantMessage: ConversationMessage = {
              role: 'assistant',
              content: proposal.assistant_message,
            }

            setState((prev) => ({
              ...prev,
              isGenerating: false,
              thinkingPhase: null,
              thinkingMessage: null,
              conversation: [...prev.conversation, userMessage, assistantMessage],
              proposal: {
                workouts: proposal.workouts,
                assistant_message: proposal.assistant_message,
              },
            }))
          },
          () => {
            // Refine endpoint doesn't emit question events
          },
          (errorMessage) => {
            setState((prev) => ({
              ...prev,
              isGenerating: false,
              thinkingPhase: null,
              thinkingMessage: null,
              error: errorMessage,
            }))
          }
        )
      } catch (e) {
        setState((prev) => ({
          ...prev,
          isGenerating: false,
          thinkingPhase: null,
          thinkingMessage: null,
          error: e instanceof Error ? e.message : 'An error occurred',
        }))
      }
    },
    [state.conversation, state.proposal, processSSEStream]
  )

  const accept = useCallback(async () => {
    if (!state.proposal) {
      setState((prev) => ({ ...prev, error: 'No proposal to accept' }))
      return
    }

    try {
      await acceptProposal(state.proposal.workouts)

      // Invalidate queries to refresh the workout list
      queryClient.invalidateQueries({ queryKey: ['planned-workouts'] })
      queryClient.invalidateQueries({ queryKey: ['calendar'] })

      // Clear the proposal after accepting
      setState((prev) => ({
        ...prev,
        proposal: null,
      }))
    } catch (e) {
      setState((prev) => ({
        ...prev,
        error: e instanceof Error ? e.message : 'Failed to save workouts',
      }))
    }
  }, [state.proposal, queryClient])

  const reject = useCallback(() => {
    setState((prev) => ({
      ...prev,
      proposal: null,
    }))
  }, [])

  const reset = useCallback(() => {
    setState({
      isGenerating: false,
      thinkingPhase: null,
      thinkingMessage: null,
      conversation: [],
      proposal: null,
      pendingQuestion: null,
      error: null,
    })
  }, [])

  return {
    ...state,
    generate,
    refine,
    accept,
    reject,
    reset,
  }
}
