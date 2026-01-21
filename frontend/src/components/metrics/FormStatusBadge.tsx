import { Badge } from '@/components/ui/badge'
import { getFormStatusColor } from '@/lib/utils'

interface FormStatusBadgeProps {
  status: string
}

export function FormStatusBadge({ status }: FormStatusBadgeProps) {
  return (
    <Badge className={getFormStatusColor(status)} variant="secondary">
      {status}
    </Badge>
  )
}
