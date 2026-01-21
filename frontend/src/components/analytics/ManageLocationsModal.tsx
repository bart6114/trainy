import { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { usePainLocations, useMergePainLocations } from '@/hooks/useAnalytics'
import { Loader2, AlertCircle, CheckCircle2 } from 'lucide-react'

interface ManageLocationsModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

type Step = 'select' | 'confirm' | 'success'

export function ManageLocationsModal({ open, onOpenChange }: ManageLocationsModalProps) {
  const { data: locations, isLoading } = usePainLocations()
  const mergeMutation = useMergePainLocations()

  const [selectedLocations, setSelectedLocations] = useState<Set<string>>(new Set())
  const [targetLocation, setTargetLocation] = useState('')
  const [useExisting, setUseExisting] = useState(true)
  const [customName, setCustomName] = useState('')
  const [step, setStep] = useState<Step>('select')
  const [updatedCount, setUpdatedCount] = useState(0)

  const handleCheckboxChange = (location: string, checked: boolean) => {
    const newSelected = new Set(selectedLocations)
    if (checked) {
      newSelected.add(location)
    } else {
      newSelected.delete(location)
    }
    setSelectedLocations(newSelected)
  }

  const selectedCount = selectedLocations.size
  const totalAffected = locations
    ?.filter((loc) => selectedLocations.has(loc.location))
    .reduce((sum, loc) => sum + loc.count, 0) ?? 0

  const handleMergeClick = () => {
    if (selectedCount < 2) return
    // Set default target to first selected location
    const firstSelected = Array.from(selectedLocations)[0]
    setTargetLocation(firstSelected)
    setUseExisting(true)
    setStep('confirm')
  }

  const handleConfirm = async () => {
    const target = useExisting ? targetLocation : customName.trim()
    if (!target) return

    try {
      const result = await mergeMutation.mutateAsync({
        source_locations: Array.from(selectedLocations),
        target_location: target,
      })
      setUpdatedCount(result.updated_count)
      setStep('success')
    } catch {
      // Error handled by mutation state
    }
  }

  const handleClose = () => {
    setSelectedLocations(new Set())
    setTargetLocation('')
    setCustomName('')
    setUseExisting(true)
    setStep('select')
    mergeMutation.reset()
    onOpenChange(false)
  }

  const handleBack = () => {
    setStep('select')
    mergeMutation.reset()
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Manage Pain Locations</DialogTitle>
          <DialogDescription>
            {step === 'select' && 'Select locations to merge into a single standardized name.'}
            {step === 'confirm' && 'Choose the target name for merged locations.'}
            {step === 'success' && 'Locations merged successfully.'}
          </DialogDescription>
        </DialogHeader>

        {step === 'select' && (
          <>
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : !locations?.length ? (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <AlertCircle className="h-8 w-8 text-muted-foreground mb-2" />
                <p className="text-sm text-muted-foreground">No pain locations recorded yet.</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-[300px] overflow-y-auto">
                {locations.map((loc) => (
                  <label
                    key={loc.location}
                    className="flex items-center gap-3 p-2 rounded-md hover:bg-accent cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={selectedLocations.has(loc.location)}
                      onChange={(e) => handleCheckboxChange(loc.location, e.target.checked)}
                      className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                    />
                    <span className="flex-1 capitalize">{loc.location}</span>
                    <span className="text-sm text-muted-foreground">
                      {loc.count} {loc.count === 1 ? 'entry' : 'entries'}
                    </span>
                  </label>
                ))}
              </div>
            )}

            <DialogFooter>
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button onClick={handleMergeClick} disabled={selectedCount < 2}>
                Merge Selected ({selectedCount})
              </Button>
            </DialogFooter>
          </>
        )}

        {step === 'confirm' && (
          <>
            <div className="space-y-4">
              <div className="p-3 bg-muted rounded-md">
                <p className="text-sm font-medium">Selected locations:</p>
                <p className="text-sm text-muted-foreground capitalize">
                  {Array.from(selectedLocations).join(', ')}
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  {totalAffected} records will be updated
                </p>
              </div>

              <div className="space-y-3">
                <Label>Merge into:</Label>
                <div className="flex items-center gap-2">
                  <input
                    type="radio"
                    id="use-existing"
                    checked={useExisting}
                    onChange={() => setUseExisting(true)}
                    className="h-4 w-4"
                  />
                  <Label htmlFor="use-existing" className="font-normal">
                    Existing location
                  </Label>
                </div>
                {useExisting && (
                  <Select value={targetLocation} onValueChange={setTargetLocation}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select location" />
                    </SelectTrigger>
                    <SelectContent>
                      {Array.from(selectedLocations).map((loc) => (
                        <SelectItem key={loc} value={loc} className="capitalize">
                          {loc}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}

                <div className="flex items-center gap-2">
                  <input
                    type="radio"
                    id="use-custom"
                    checked={!useExisting}
                    onChange={() => setUseExisting(false)}
                    className="h-4 w-4"
                  />
                  <Label htmlFor="use-custom" className="font-normal">
                    New name
                  </Label>
                </div>
                {!useExisting && (
                  <Input
                    placeholder="e.g., Left Knee"
                    value={customName}
                    onChange={(e) => setCustomName(e.target.value)}
                  />
                )}
              </div>

              {mergeMutation.isError && (
                <div className="flex items-center gap-2 text-sm text-destructive">
                  <AlertCircle className="h-4 w-4" />
                  Failed to merge locations. Please try again.
                </div>
              )}
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={handleBack}>
                Back
              </Button>
              <Button
                onClick={handleConfirm}
                disabled={
                  mergeMutation.isPending ||
                  (useExisting ? !targetLocation : !customName.trim())
                }
              >
                {mergeMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                Confirm Merge
              </Button>
            </DialogFooter>
          </>
        )}

        {step === 'success' && (
          <>
            <div className="flex flex-col items-center justify-center py-6 text-center">
              <CheckCircle2 className="h-12 w-12 text-green-500 mb-3" />
              <p className="font-medium">Merge Complete</p>
              <p className="text-sm text-muted-foreground">
                {updatedCount} {updatedCount === 1 ? 'record was' : 'records were'} updated.
              </p>
            </div>

            <DialogFooter>
              <Button onClick={handleClose}>Done</Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
