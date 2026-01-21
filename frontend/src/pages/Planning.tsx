import { useState } from 'react'
import { format, parseISO } from 'date-fns'
import { Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useGenerateWorkouts, useUpcomingWorkouts, useDeleteWorkout, useSkipWorkout } from '@/hooks/usePlanning'
import { formatDuration } from '@/lib/utils'
import type { PlannedWorkout } from '@/types'

function WorkoutCard({ workout, onDelete, onSkip }: { workout: PlannedWorkout; onDelete: () => void; onSkip: () => void }) {
  return (
    <div className="flex items-start justify-between p-4 rounded-md border">
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <Badge variant="outline">{workout.activity_type}</Badge>
          {workout.workout_type && (
            <Badge variant="secondary">{workout.workout_type}</Badge>
          )}
          <span className="font-medium">{workout.title}</span>
        </div>
        <p className="text-sm text-muted-foreground mb-2">
          {format(parseISO(workout.planned_date), 'EEEE, MMMM d, yyyy')}
        </p>
        {workout.description && (
          <p className="text-sm text-muted-foreground mb-2">{workout.description}</p>
        )}
        <div className="flex gap-4 text-sm">
          {workout.target_duration_s && (
            <span>Duration: {formatDuration(workout.target_duration_s)}</span>
          )}
          {workout.target_tss && (
            <span>TSS: {Math.round(workout.target_tss)}</span>
          )}
        </div>
      </div>
      <div className="flex gap-2 ml-4">
        {workout.status === 'planned' && (
          <>
            <Button variant="ghost" size="sm" onClick={onSkip}>
              Skip
            </Button>
            <Button variant="ghost" size="icon" onClick={onDelete}>
              <Trash2 className="h-4 w-4" />
            </Button>
          </>
        )}
        {workout.status === 'completed' && (
          <Badge className="bg-green-100 text-green-800">Completed</Badge>
        )}
        {workout.status === 'skipped' && (
          <Badge variant="secondary">Skipped</Badge>
        )}
      </div>
    </div>
  )
}

export function Planning() {
  const [prompt, setPrompt] = useState('')
  const { data: upcomingWorkouts, isLoading: workoutsLoading } = useUpcomingWorkouts(30)
  const generateWorkouts = useGenerateWorkouts()
  const deleteWorkout = useDeleteWorkout()
  const skipWorkout = useSkipWorkout()

  const handleGenerate = async () => {
    if (!prompt.trim()) return
    await generateWorkouts.mutateAsync(prompt)
    setPrompt('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey && e.metaKey) {
      e.preventDefault()
      handleGenerate()
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Workout Planning</h1>
        <p className="text-muted-foreground">Generate and manage your AI-powered training workouts</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Generate Workouts</CardTitle>
          <CardDescription>
            Describe your training goals and preferences. The AI will generate specific workouts for you.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea
            placeholder="E.g., 'I want to train for a 10K race in 8 weeks. I can run 4 days per week and do 1 strength session.'"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={4}
            disabled={generateWorkouts.isPending}
          />
          <div className="flex justify-between items-center">
            <p className="text-xs text-muted-foreground">Press Cmd+Enter to generate</p>
            <Button
              onClick={handleGenerate}
              disabled={!prompt.trim() || generateWorkouts.isPending}
            >
              {generateWorkouts.isPending ? 'Generating...' : 'Generate Workouts'}
            </Button>
          </div>
          {generateWorkouts.isError && (
            <p className="text-sm text-destructive">
              An error occurred. Please make sure the OpenRouter API key is configured and try again.
            </p>
          )}
          {generateWorkouts.isSuccess && (
            <p className="text-sm text-green-600">
              Generated {generateWorkouts.data.count} workouts!
            </p>
          )}
        </CardContent>
      </Card>

      <div>
        <h2 className="text-xl font-semibold mb-4">Planned Workouts</h2>
        {workoutsLoading ? (
          <p className="text-muted-foreground">Loading workouts...</p>
        ) : upcomingWorkouts && upcomingWorkouts.workouts.length > 0 ? (
          <div className="space-y-3">
            {upcomingWorkouts.workouts.map((workout) => (
              <WorkoutCard
                key={workout.id}
                workout={workout}
                onDelete={() => deleteWorkout.mutate(workout.id)}
                onSkip={() => skipWorkout.mutate(workout.id)}
              />
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="pt-6">
              <p className="text-muted-foreground text-center">
                No planned workouts yet. Generate some workouts using the form above!
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
