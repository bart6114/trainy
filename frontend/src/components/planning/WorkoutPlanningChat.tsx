import { useState, useRef, useEffect } from 'react'
import { format, parseISO } from 'date-fns'
import { Send, Loader2, X, Check, Calendar, Dumbbell } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { useConversationalPlanning } from '@/hooks/useConversationalPlanning'
import { formatDuration } from '@/lib/utils'
import type { ConversationMessage, ProposedWorkout, QuestionEvent } from '@/types'

function ThinkingBubble({ message }: { message: string }) {
  return (
    <div className="flex justify-start">
      <div className="bg-muted rounded-lg px-4 py-3 max-w-[85%]">
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            <span className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce [animation-delay:-0.3s]" />
            <span className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce [animation-delay:-0.15s]" />
            <span className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" />
          </div>
          <span className="text-sm text-muted-foreground">{message}</span>
        </div>
      </div>
    </div>
  )
}

function MessageBubble({ message }: { message: ConversationMessage }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] rounded-lg px-4 py-2 ${
          isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'
        }`}
      >
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
      </div>
    </div>
  )
}

function QuestionOptions({
  options,
  onSelect,
}: {
  options: string[]
  onSelect: (option: string) => void
}) {
  return (
    <div className="flex justify-start">
      <div className="flex flex-wrap gap-2 max-w-[85%]">
        {options.map((option, index) => (
          <Button
            key={index}
            variant="outline"
            size="sm"
            onClick={() => onSelect(option)}
            className="text-xs"
          >
            {option}
          </Button>
        ))}
      </div>
    </div>
  )
}

function ProposedWorkoutCard({ workout }: { workout: ProposedWorkout }) {
  return (
    <div className="flex items-start gap-3 p-3 rounded-lg border bg-card">
      <div className="flex-shrink-0 w-12 text-center">
        <div className="text-xs text-muted-foreground font-medium">
          {format(parseISO(workout.date), 'EEE')}
        </div>
        <div className="text-xl font-bold">
          {format(parseISO(workout.date), 'd')}
        </div>
        <div className="text-xs text-muted-foreground">
          {format(parseISO(workout.date), 'MMM')}
        </div>
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1 flex-wrap">
          <Badge variant="outline" className="text-xs">
            {workout.activity_type}
          </Badge>
          {workout.workout_type && (
            <Badge variant="secondary" className="text-xs">
              {workout.workout_type}
            </Badge>
          )}
        </div>
        <p className="font-medium text-sm">{workout.title}</p>
        {workout.description && (
          <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
            {workout.description}
          </p>
        )}
        <div className="flex gap-3 mt-2 text-xs text-muted-foreground">
          {workout.target_duration_minutes > 0 && (
            <span>{formatDuration(workout.target_duration_minutes * 60)}</span>
          )}
          {workout.target_tss && <span>TSS: {workout.target_tss}</span>}
        </div>
      </div>
    </div>
  )
}

function EmptyWorkoutsPanel() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center p-8">
      <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
        <Calendar className="w-8 h-8 text-muted-foreground" />
      </div>
      <p className="text-muted-foreground text-sm">
        Your proposed workouts will appear here
      </p>
      <p className="text-muted-foreground text-xs mt-1">
        Start by describing your training goals in the chat
      </p>
    </div>
  )
}

function ChatPanel({
  conversation,
  thinkingMessage,
  isGenerating,
  hasProposal,
  pendingQuestion,
  input,
  setInput,
  onSubmit,
  onOptionSelect,
}: {
  conversation: ConversationMessage[]
  thinkingMessage: string | null
  isGenerating: boolean
  hasProposal: boolean
  pendingQuestion: QuestionEvent | null
  input: string
  setInput: (value: string) => void
  onSubmit: (e: React.FormEvent) => void
  onOptionSelect: (option: string) => void
}) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [conversation, thinkingMessage, pendingQuestion])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSubmit(e)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {conversation.length === 0 && !isGenerating && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-muted-foreground">
              <Dumbbell className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">Describe your training goals</p>
              <p className="text-xs mt-1">
                e.g., "4-week plan to improve my 10K"
              </p>
            </div>
          </div>
        )}

        {conversation.map((message, index) => (
          <MessageBubble key={index} message={message} />
        ))}

        {pendingQuestion?.options && pendingQuestion.options.length > 0 && (
          <QuestionOptions
            options={pendingQuestion.options}
            onSelect={onOptionSelect}
          />
        )}

        {isGenerating && thinkingMessage && (
          <ThinkingBubble message={thinkingMessage} />
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={onSubmit} className="p-4 border-t">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              pendingQuestion
                ? 'Answer the question...'
                : hasProposal
                  ? 'Describe changes...'
                  : 'Describe your training goals...'
            }
            disabled={isGenerating}
            className="flex-1"
          />
          <Button
            type="submit"
            disabled={!input.trim() || isGenerating}
            size="icon"
          >
            {isGenerating ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </form>
    </div>
  )
}

function WorkoutsPanel({
  workouts,
  onAccept,
  onDiscard,
  isAccepting,
}: {
  workouts: ProposedWorkout[] | null
  onAccept: () => void
  onDiscard: () => void
  isAccepting: boolean
}) {
  if (!workouts) {
    return <EmptyWorkoutsPanel />
  }

  return (
    <div className="flex flex-col h-full">
      {/* Sticky header with actions */}
      <div className="flex items-center justify-between p-4 border-b bg-background">
        <div className="text-sm font-medium">
          {workouts.length} workout{workouts.length !== 1 ? 's' : ''} proposed
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onDiscard}
            disabled={isAccepting}
          >
            <X className="h-4 w-4 mr-1" />
            Discard
          </Button>
          <Button size="sm" onClick={onAccept} disabled={isAccepting}>
            {isAccepting ? (
              <Loader2 className="h-4 w-4 mr-1 animate-spin" />
            ) : (
              <Check className="h-4 w-4 mr-1" />
            )}
            Accept & Save
          </Button>
        </div>
      </div>

      {/* Scrollable workout list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {workouts.map((workout, index) => (
          <ProposedWorkoutCard key={`${workout.date}-${index}`} workout={workout} />
        ))}
      </div>
    </div>
  )
}

export function WorkoutPlanningChat() {
  const [input, setInput] = useState('')
  const [isAccepting, setIsAccepting] = useState(false)

  const {
    isGenerating,
    thinkingMessage,
    conversation,
    proposal,
    pendingQuestion,
    error,
    generate,
    refine,
    accept,
    reject,
  } = useConversationalPlanning()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isGenerating) return

    const trimmedInput = input.trim()
    setInput('')

    // If there's a pending question or no proposal, use generate
    // (answers to questions go through generate to continue the flow)
    if (pendingQuestion || !proposal) {
      generate(trimmedInput)
    } else {
      refine(trimmedInput)
    }
  }

  const handleOptionSelect = (option: string) => {
    if (isGenerating) return
    generate(option)
  }

  const handleAccept = async () => {
    setIsAccepting(true)
    try {
      await accept()
    } finally {
      setIsAccepting(false)
    }
  }

  return (
    <div className="border rounded-lg overflow-hidden">
      {/* Split layout container */}
      <div className="flex h-[500px]">
        {/* Left: Chat panel (40%) */}
        <div className="w-[40%] border-r flex flex-col">
          <ChatPanel
            conversation={conversation}
            thinkingMessage={thinkingMessage}
            isGenerating={isGenerating}
            hasProposal={!!proposal}
            pendingQuestion={pendingQuestion}
            input={input}
            setInput={setInput}
            onSubmit={handleSubmit}
            onOptionSelect={handleOptionSelect}
          />
        </div>

        {/* Right: Workouts panel (60%) */}
        <div className="w-[60%] bg-muted/30">
          <WorkoutsPanel
            workouts={proposal?.workouts ?? null}
            onAccept={handleAccept}
            onDiscard={reject}
            isAccepting={isAccepting}
          />
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="p-3 border-t bg-destructive/10">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}
    </div>
  )
}
