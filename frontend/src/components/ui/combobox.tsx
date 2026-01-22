import * as React from 'react'
import * as Popover from '@radix-ui/react-popover'
import { cn } from '@/lib/utils'

interface ComboboxProps {
  value: string
  onChange: (value: string) => void
  options: string[]
  placeholder?: string
  className?: string
}

export function Combobox({
  value,
  onChange,
  options,
  placeholder,
  className,
}: ComboboxProps) {
  const [open, setOpen] = React.useState(false)
  const [highlightedIndex, setHighlightedIndex] = React.useState(0)
  const inputRef = React.useRef<HTMLInputElement>(null)
  const listRef = React.useRef<HTMLDivElement>(null)

  const filteredOptions = React.useMemo(() => {
    if (!value.trim()) return options
    const lower = value.toLowerCase()
    return options.filter((opt) => opt.toLowerCase().includes(lower))
  }, [value, options])

  React.useEffect(() => {
    setHighlightedIndex(0)
  }, [filteredOptions])

  const selectOption = (option: string) => {
    onChange(option)
    setOpen(false)
    inputRef.current?.blur()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!open && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) {
      setOpen(true)
      return
    }

    if (!open) return

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setHighlightedIndex((i) =>
          i < filteredOptions.length - 1 ? i + 1 : 0
        )
        break
      case 'ArrowUp':
        e.preventDefault()
        setHighlightedIndex((i) =>
          i > 0 ? i - 1 : filteredOptions.length - 1
        )
        break
      case 'Enter':
        e.preventDefault()
        if (filteredOptions[highlightedIndex]) {
          selectOption(filteredOptions[highlightedIndex])
        }
        break
      case 'Escape':
        e.preventDefault()
        setOpen(false)
        break
    }
  }

  React.useEffect(() => {
    if (open && listRef.current) {
      const highlighted = listRef.current.children[highlightedIndex] as HTMLElement
      highlighted?.scrollIntoView({ block: 'nearest' })
    }
  }, [highlightedIndex, open])

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Anchor asChild>
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => {
            onChange(e.target.value)
            if (!open) setOpen(true)
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className={cn(
            'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
            className
          )}
        />
      </Popover.Anchor>
      <Popover.Portal>
        <Popover.Content
          align="start"
          sideOffset={4}
          onOpenAutoFocus={(e) => e.preventDefault()}
          className="z-50 w-[var(--radix-popover-trigger-width)] max-h-60 overflow-auto rounded-md border bg-popover text-popover-foreground shadow-md data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95"
        >
          <div ref={listRef} className="p-1">
            {filteredOptions.length === 0 ? (
              <div className="py-2 px-3 text-sm text-muted-foreground">
                {value.trim() ? 'No matches — press Enter to use as-is' : 'No options available'}
              </div>
            ) : (
              filteredOptions.map((option, index) => (
                <div
                  key={option}
                  onClick={() => selectOption(option)}
                  className={cn(
                    'relative flex cursor-pointer select-none items-center rounded-sm py-1.5 px-3 text-sm outline-none',
                    index === highlightedIndex
                      ? 'bg-accent text-accent-foreground'
                      : 'hover:bg-accent hover:text-accent-foreground'
                  )}
                >
                  {option}
                </div>
              ))
            )}
          </div>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  )
}
