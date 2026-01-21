import { useState } from 'react'
import { format, subDays } from 'date-fns'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useImportStatus, useImport } from '@/hooks/useImport'
import { Upload, CheckCircle, Loader2 } from 'lucide-react'

export function ImportSection() {
  const [fromDate, setFromDate] = useState(format(subDays(new Date(), 30), 'yyyy-MM-dd'))
  const { data: status } = useImportStatus()
  const { isRunning, progress, total, imported, skipped, errors, currentFile, lastError, startImport, cancelImport } = useImport()

  const progressPercent = total > 0 ? (progress / total) * 100 : 0

  return (
    <Card>
      <CardHeader>
        <CardTitle>Import Activities</CardTitle>
        <CardDescription>
          Import FIT files from your RunGap export folder
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {status && (
          <p className="text-sm text-muted-foreground">
            {status.message}
          </p>
        )}

        <div className="space-y-2">
          <Label htmlFor="fromDate">Import activities from date</Label>
          <div className="flex gap-2">
            <Input
              id="fromDate"
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
              disabled={isRunning}
            />
            <Button
              variant="outline"
              onClick={() => setFromDate(format(subDays(new Date(), 7), 'yyyy-MM-dd'))}
              disabled={isRunning}
            >
              Last Week
            </Button>
          </div>
        </div>

        {isRunning ? (
          <div className="space-y-4">
            <Progress value={progressPercent} className="h-2" />
            <div className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                {currentFile ? `Processing: ${currentFile}` : 'Starting...'}
              </span>
              <span>{progress} / {total}</span>
            </div>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-green-600">{imported}</div>
                <div className="text-xs text-muted-foreground">Imported</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-yellow-600">{skipped}</div>
                <div className="text-xs text-muted-foreground">Skipped</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-red-600">{errors}</div>
                <div className="text-xs text-muted-foreground">Errors</div>
              </div>
            </div>
            {lastError && (
              <p className="text-sm text-destructive">{lastError}</p>
            )}
            <Button variant="outline" onClick={cancelImport}>
              Cancel Import
            </Button>
          </div>
        ) : (
          <>
            {imported > 0 && (
              <div className="flex items-center gap-2 p-4 rounded-md bg-green-50 text-green-800 dark:bg-green-950 dark:text-green-200">
                <CheckCircle className="h-5 w-5" />
                <span>Import complete: {imported} imported, {skipped} skipped, {errors} errors</span>
              </div>
            )}
            <Button onClick={() => startImport(fromDate)} disabled={!status?.available}>
              <Upload className="h-4 w-4 mr-2" />
              Start Import
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  )
}
