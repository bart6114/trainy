import { useState, useRef, useEffect } from 'react'
import { format, parseISO } from 'date-fns'
import { Send, Loader2, X, Check, Calendar, MessageSquare, Wrench, Pencil, Trash2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { useCoachingChat } from '@/hooks/useCoachingChat'
import { formatDuration } from '@/lib/utils'
import type { CoachingMessage, ToolCallInfo, ToolResultInfo, WorkoutProposalItem, WorkoutDeletionItem } from '@/types'

// Tool name to human-readable label mapping
const TOOL_LABELS: Record<string, string> = {
  get_recent_activities: 'Checking recent activities',
  get_fitness_state: 'Checking fitness status',
  get_pain_history: 'Reviewing injury history',
  get_wellness_trends: 'Analyzing wellness trends',
  get_power_curve: 'Analyzing power data',
  get_planned_workouts: 'Checking planned workouts',
  create_workouts: 'Creating workout plan',
  modify_workout: 'Modifying workout',
  delete_workout: 'Removing workout',
}

function ThinkingIndicator({ message }: { message: string }) {
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

function ToolCallIndicator({ toolCall }: { toolCall: ToolCallInfo }) {
  const label = TOOL_LABELS[toolCall.tool_name] || toolCall.tool_name

  return (
    <div className="flex justify-start">
      <div className="bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-lg px-3 py-2 max-w-[85%]">
        <div className="flex items-center gap-2">
          <Wrench className="w-4 h-4 text-blue-500 animate-spin" />
          <span className="text-sm text-blue-700 dark:text-blue-300">{label}...</span>
        </div>
      </div>
    </div>
  )
}

function ToolResultBadge({ result }: { result: ToolResultInfo }) {
  const label = TOOL_LABELS[result.tool_name] || result.tool_name

  return (
    <div className="flex items-center gap-1.5 text-xs text-muted-foreground bg-muted/50 rounded px-2 py-1">
      <Wrench className="w-3 h-3" />
      <span className="font-medium">{label.replace(/^(Checking|Reviewing|Analyzing|Creating|Modifying|Removing)\s+/i, '')}</span>
      <span className="text-muted-foreground/70">- {result.summary}</span>
    </div>
  )
}

function MessageBubble({ message }: { message: CoachingMessage }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
      {/* Show tool results summary for assistant messages */}
      {!isUser && message.toolResults && message.toolResults.length > 0 && (
        <div className="mb-2 space-y-1 max-w-[85%]">
          {message.toolResults.map((result, index) => (
            <ToolResultBadge key={index} result={result} />
          ))}
        </div>
      )}

      <div
        className={`max-w-[85%] rounded-lg px-4 py-2 ${
          isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'
        }`}
      >
        {isUser ? (
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="text-sm prose prose-sm dark:prose-invert prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0 prose-headings:my-2 prose-headings:font-semibold prose-table:my-2 prose-th:px-2 prose-th:py-1 prose-td:px-2 prose-td:py-1 max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}

function ProposedWorkoutCard({ workout }: { workout: WorkoutProposalItem }) {
  const isEdit = !!workout.existing_workout_id

  return (
    <div className={`flex items-start gap-3 p-3 rounded-lg border bg-card ${isEdit ? 'border-amber-500/50 bg-amber-50/30 dark:bg-amber-950/20' : ''}`}>
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
          {isEdit && (
            <Badge variant="outline" className="text-xs bg-amber-100 text-amber-700 border-amber-300 dark:bg-amber-900/50 dark:text-amber-400 dark:border-amber-700">
              <Pencil className="w-3 h-3 mr-1" />
              Editing
            </Badge>
          )}
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
          {workout.target_calories && <span>{workout.target_calories} kcal</span>}
        </div>
      </div>
    </div>
  )
}

function DeletionCard({ deletion }: { deletion: WorkoutDeletionItem }) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-lg border border-red-300 bg-red-50/50 dark:bg-red-950/20 dark:border-red-800">
      <Trash2 className="w-5 h-5 text-red-500 flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm text-red-700 dark:text-red-400">{deletion.title}</p>
        <p className="text-xs text-red-600/70 dark:text-red-400/70">
          {format(parseISO(deletion.date), 'EEE, MMM d')} - Will be deleted
        </p>
      </div>
    </div>
  )
}

function EmptyProposalPanel() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center p-8">
      <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
        <Calendar className="w-8 h-8 text-muted-foreground" />
      </div>
      <p className="text-muted-foreground text-sm">
        Workout proposals will appear here
      </p>
      <p className="text-muted-foreground text-xs mt-1">
        Ask the coach to plan workouts for you
      </p>
    </div>
  )
}

function ChatPanel({
  conversation,
  thinkingMessage,
  activeToolCall,
  isProcessing,
  hasProposal,
  input,
  setInput,
  onSubmit,
}: {
  conversation: CoachingMessage[]
  thinkingMessage: string | null
  activeToolCall: ToolCallInfo | null
  isProcessing: boolean
  hasProposal: boolean
  input: string
  setInput: (value: string) => void
  onSubmit: (e: React.FormEvent) => void
}) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [conversation, thinkingMessage, activeToolCall])

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
        {conversation.length === 0 && !isProcessing && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-muted-foreground">
              <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">Chat with your AI coach</p>
              <p className="text-xs mt-1">
                Ask about training, plan workouts, or get insights
              </p>
            </div>
          </div>
        )}

        {conversation.map((message, index) => (
          <MessageBubble key={index} message={message} />
        ))}

        {isProcessing && thinkingMessage && !activeToolCall && (
          <ThinkingIndicator message={thinkingMessage} />
        )}

        {isProcessing && activeToolCall && (
          <ToolCallIndicator toolCall={activeToolCall} />
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
              hasProposal
                ? 'Ask to modify the plan...'
                : 'Ask about training or plan workouts...'
            }
            disabled={isProcessing}
            className="flex-1"
          />
          <Button
            type="submit"
            disabled={!input.trim() || isProcessing}
            size="icon"
          >
            {isProcessing ? (
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

function ProposalPanel({
  workouts,
  deletions,
  onAccept,
  onReject,
  isAccepting,
}: {
  workouts: WorkoutProposalItem[]
  deletions: WorkoutDeletionItem[]
  onAccept: () => void
  onReject: () => void
  isAccepting: boolean
}) {
  const hasChanges = workouts.length > 0 || deletions.length > 0

  if (!hasChanges) {
    return <EmptyProposalPanel />
  }

  const editCount = workouts.filter((w) => w.existing_workout_id).length
  const newCount = workouts.length - editCount
  const deleteCount = deletions.length

  return (
    <div className="flex flex-col h-full">
      {/* Sticky header with actions */}
      <div className="flex items-center justify-between p-4 border-b bg-background">
        <div className="text-sm font-medium">
          {newCount > 0 && <span>{newCount} new</span>}
          {newCount > 0 && editCount > 0 && <span>, </span>}
          {editCount > 0 && (
            <span className="text-amber-600 dark:text-amber-400">
              {editCount} edit{editCount !== 1 ? 's' : ''}
            </span>
          )}
          {(newCount > 0 || editCount > 0) && deleteCount > 0 && <span>, </span>}
          {deleteCount > 0 && (
            <span className="text-red-600 dark:text-red-400">
              {deleteCount} deletion{deleteCount !== 1 ? 's' : ''}
            </span>
          )}
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onReject}
            disabled={isAccepting}
          >
            <X className="h-4 w-4 mr-1" />
            Reject
          </Button>
          <Button size="sm" onClick={onAccept} disabled={isAccepting}>
            {isAccepting ? (
              <Loader2 className="h-4 w-4 mr-1 animate-spin" />
            ) : (
              <Check className="h-4 w-4 mr-1" />
            )}
            Accept All
          </Button>
        </div>
      </div>

      {/* Scrollable proposal content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {/* Deletions first */}
        {deletions.map((deletion) => (
          <DeletionCard key={deletion.workout_id} deletion={deletion} />
        ))}

        {/* Then workouts */}
        {workouts.map((workout, index) => (
          <ProposedWorkoutCard key={`${workout.date}-${index}`} workout={workout} />
        ))}
      </div>
    </div>
  )
}

export function CoachingChat() {
  const [input, setInput] = useState('')
  const [isAccepting, setIsAccepting] = useState(false)

  const {
    isProcessing,
    thinkingMessage,
    activeToolCall,
    conversation,
    proposal,
    error,
    sendMessage,
    acceptProposal,
    rejectProposal,
    clearError,
  } = useCoachingChat()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isProcessing) return

    const trimmedInput = input.trim()
    setInput('')
    sendMessage(trimmedInput)
  }

  const handleAccept = async () => {
    setIsAccepting(true)
    try {
      await acceptProposal()
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
            activeToolCall={activeToolCall}
            isProcessing={isProcessing}
            hasProposal={!!proposal}
            input={input}
            setInput={setInput}
            onSubmit={handleSubmit}
          />
        </div>

        {/* Right: Proposal panel (60%) */}
        <div className="w-[60%] bg-muted/30">
          <ProposalPanel
            workouts={proposal?.workouts ?? []}
            deletions={proposal?.deletions ?? []}
            onAccept={handleAccept}
            onReject={rejectProposal}
            isAccepting={isAccepting}
          />
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="p-3 border-t bg-destructive/10 flex items-center justify-between">
          <p className="text-sm text-destructive">{error}</p>
          <Button variant="ghost" size="sm" onClick={clearError}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  )
}
