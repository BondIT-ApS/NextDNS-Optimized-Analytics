import React, { memo, useRef, useEffect } from 'react'
import { Input } from '@/components/ui/input'
import { Search } from 'lucide-react'

interface SearchInputProps {
  value: string
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  placeholder?: string
}

export const SearchInput = memo<SearchInputProps>(({ value, onChange, placeholder = "Search..." }) => {
  const inputRef = useRef<HTMLInputElement>(null)
  const lastFocusedRef = useRef<boolean>(false)

  // Track if input was focused and restore it after re-renders
  useEffect(() => {
    const input = inputRef.current
    if (input && lastFocusedRef.current) {
      const cursorPosition = input.selectionStart
      input.focus()
      if (cursorPosition !== null) {
        input.setSelectionRange(cursorPosition, cursorPosition)
      }
    }
  })

  const handleFocus = () => {
    lastFocusedRef.current = true
  }

  const handleBlur = () => {
    lastFocusedRef.current = false
  }

  return (
    <div className="relative flex-1">
      <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
      <Input
        ref={inputRef}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        onFocus={handleFocus}
        onBlur={handleBlur}
        className="pl-10"
      />
    </div>
  )
})

SearchInput.displayName = 'SearchInput'