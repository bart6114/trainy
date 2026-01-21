import { ThresholdsForm } from '@/components/settings/ThresholdsForm'
import { ImportSection } from '@/components/settings/ImportSection'
import { DangerZone } from '@/components/settings/DangerZone'

export function Settings() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">Manage your profile and import activities</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <ThresholdsForm />
        <ImportSection />
      </div>

      <DangerZone />
    </div>
  )
}
