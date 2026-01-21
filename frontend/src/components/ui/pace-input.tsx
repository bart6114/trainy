import * as React from 'react'
import { cn } from '@/lib/utils'

function decimalToMmss(decimal: number): string {
  const minutes = Math.floor(decimal)
  const seconds = Math.round((decimal - minutes) * 60)
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
}

function mmssToDecimal(mmss: string): number | null {
  const match = mmss.match(/^(\d+):(\d{1,2})$/)
  if (match) {
    const minutes = parseInt(match[1], 10)
    const seconds = parseInt(match[2], 10)
    if (seconds < 60) {
      return minutes + seconds / 60
    }
  }
  const num = parseFloat(mmss)
  if (!isNaN(num)) {
    return num
  }
  return null
}

export interface PaceInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'value' | 'onChange'> {
  value?: number
  onChange?: (value: number) => void
}

const PaceInput = React.forwardRef<HTMLInputElement, PaceInputProps>(
  ({ className, value, onChange, onBlur, ...props }, ref) => {
    const [displayValue, setDisplayValue] = React.useState('')

    React.useEffect(() => {
      if (value !== undefined && !isNaN(value)) {
        setDisplayValue(decimalToMmss(value))
      }
    }, [value])

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      setDisplayValue(e.target.value)
    }

    const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
      const decimal = mmssToDecimal(displayValue)
      if (decimal !== null) {
        setDisplayValue(decimalToMmss(decimal))
        onChange?.(decimal)
      }
      onBlur?.(e)
    }

    return (
      <input
        type="text"
        className={cn(
          'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
          className
        )}
        ref={ref}
        value={displayValue}
        onChange={handleChange}
        onBlur={handleBlur}
        placeholder="4:30"
        {...props}
      />
    )
  }
)
PaceInput.displayName = 'PaceInput'

export { PaceInput, decimalToMmss, mmssToDecimal }
