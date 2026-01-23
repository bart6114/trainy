import { useState } from 'react'
import { useActivities } from '@/hooks/useActivities'
import { ActivityTable } from '@/components/activities/ActivityTable'
import { ActivityCard } from '@/components/activities/ActivityCard'
import { ActivityDetailSheet } from '@/components/activities/ActivityDetailSheet'
import { Button } from '@/components/ui/button'
import { ChevronLeft, ChevronRight, Grid, List } from 'lucide-react'

export function Activities() {
  const [page, setPage] = useState(0)
  const [view, setView] = useState<'table' | 'cards'>('table')
  const [selectedActivityId, setSelectedActivityId] = useState<number | null>(null)
  const limit = 20
  const { data, isLoading } = useActivities(page * limit, limit)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Activities</h1>
          <p className="text-muted-foreground">
            {data ? `${data.total} total activities` : 'Loading...'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant={view === 'table' ? 'default' : 'outline'} size="icon" onClick={() => setView('table')}>
            <List className="h-4 w-4" />
          </Button>
          <Button variant={view === 'cards' ? 'default' : 'outline'} size="icon" onClick={() => setView('cards')}>
            <Grid className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-8 text-muted-foreground">Loading activities...</div>
      ) : data && data.items.length > 0 ? (
        <>
          {view === 'table' ? (
            <ActivityTable
              activities={data.items}
              onSelect={(activity) => setSelectedActivityId(activity.id)}
            />
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {data.items.map((activity) => (
                <ActivityCard
                  key={activity.id}
                  activity={activity}
                  onClick={() => setSelectedActivityId(activity.id)}
                />
              ))}
            </div>
          )}

          {/* Pagination */}
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Showing {page * limit + 1} to {Math.min((page + 1) * limit, data.total)} of {data.total}
            </p>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0}>
                <ChevronLeft className="h-4 w-4 mr-1" /> Previous
              </Button>
              <Button variant="outline" size="sm" onClick={() => setPage(page + 1)} disabled={!data.has_more}>
                Next <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          </div>
        </>
      ) : (
        <div className="text-center py-8 text-muted-foreground">
          No activities found. Import some FIT files to get started!
        </div>
      )}

      <ActivityDetailSheet
        activityId={selectedActivityId}
        open={selectedActivityId !== null}
        onOpenChange={(open) => !open && setSelectedActivityId(null)}
      />
    </div>
  )
}
