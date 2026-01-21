import { useState } from 'react'
import { AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import {
  useDataStats,
  useDeleteAllData,
  useDeleteAllActivities,
  useDeleteAllPlannedWorkouts,
} from '@/hooks/useDangerZone'

type DeleteAction = 'activities' | 'planned-workouts' | 'all' | null

export function DangerZone() {
  const { data: stats } = useDataStats()
  const deleteAllData = useDeleteAllData()
  const deleteActivities = useDeleteAllActivities()
  const deletePlannedWorkouts = useDeleteAllPlannedWorkouts()

  const [dialogOpen, setDialogOpen] = useState(false)
  const [deleteAction, setDeleteAction] = useState<DeleteAction>(null)
  const [confirmText, setConfirmText] = useState('')

  const openDialog = (action: DeleteAction) => {
    setDeleteAction(action)
    setConfirmText('')
    setDialogOpen(true)
  }

  const closeDialog = () => {
    setDialogOpen(false)
    setDeleteAction(null)
    setConfirmText('')
  }

  const handleDelete = async () => {
    if (confirmText !== 'DELETE') return

    switch (deleteAction) {
      case 'activities':
        await deleteActivities.mutateAsync()
        break
      case 'planned-workouts':
        await deletePlannedWorkouts.mutateAsync()
        break
      case 'all':
        await deleteAllData.mutateAsync()
        break
    }
    closeDialog()
  }

  const isDeleting =
    deleteAllData.isPending ||
    deleteActivities.isPending ||
    deletePlannedWorkouts.isPending

  const getDialogContent = () => {
    switch (deleteAction) {
      case 'activities':
        return {
          title: 'Delete All Activities',
          description: `This will permanently delete ${stats?.activities ?? 0} activities, ${stats?.activity_metrics ?? 0} activity metrics, ${stats?.daily_metrics ?? 0} daily metrics, and related feedback. Planned workouts will be unlinked but preserved.`,
        }
      case 'planned-workouts':
        return {
          title: 'Delete All Planned Workouts',
          description: `This will permanently delete ${stats?.planned_workouts ?? 0} planned workouts from your calendar.`,
        }
      case 'all':
        return {
          title: 'Delete All Data',
          description: `This will permanently delete all your data: ${stats?.activities ?? 0} activities, ${stats?.planned_workouts ?? 0} planned workouts, ${stats?.activity_metrics ?? 0} activity metrics, ${stats?.daily_metrics ?? 0} daily metrics, and ${stats?.workout_feedback ?? 0} feedback entries. Your profile settings will be preserved.`,
        }
      default:
        return { title: '', description: '' }
    }
  }

  const dialogContent = getDialogContent()

  return (
    <>
      <Card className="border-destructive/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-destructive">
            <AlertTriangle className="h-5 w-5" />
            Danger Zone
          </CardTitle>
          <CardDescription>
            Irreversible actions that delete your data
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <h4 className="font-medium">Delete All Activities</h4>
            <p className="text-sm text-muted-foreground">
              Removes imported activities, metrics, and training load data.
              Planned workouts will be unlinked but preserved.
            </p>
            <Button
              variant="destructive"
              onClick={() => openDialog('activities')}
              disabled={isDeleting || !stats?.activities}
            >
              Delete All Activities ({stats?.activities ?? 0})
            </Button>
          </div>

          <div className="space-y-2">
            <h4 className="font-medium">Delete All Planned Workouts</h4>
            <p className="text-sm text-muted-foreground">
              Removes all scheduled workouts from your calendar.
            </p>
            <Button
              variant="destructive"
              onClick={() => openDialog('planned-workouts')}
              disabled={isDeleting || !stats?.planned_workouts}
            >
              Delete Planned Workouts ({stats?.planned_workouts ?? 0})
            </Button>
          </div>

          <div className="space-y-2">
            <h4 className="font-medium">Delete Everything</h4>
            <p className="text-sm text-muted-foreground">
              Removes all data except your profile settings.
            </p>
            <Button
              variant="destructive"
              onClick={() => openDialog('all')}
              disabled={isDeleting || (!stats?.activities && !stats?.planned_workouts)}
            >
              Delete All Data
            </Button>
          </div>
        </CardContent>
      </Card>

      <AlertDialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="h-5 w-5" />
              {dialogContent.title}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {dialogContent.description}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="space-y-2 py-4">
            <p className="text-sm font-medium">
              Type <span className="font-mono text-destructive">DELETE</span> to confirm:
            </p>
            <Input
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              placeholder="Type DELETE to confirm"
              autoComplete="off"
            />
          </div>
          <AlertDialogFooter>
            <Button variant="outline" onClick={closeDialog}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={confirmText !== 'DELETE' || isDeleting}
            >
              {isDeleting ? 'Deleting...' : 'Delete Permanently'}
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
