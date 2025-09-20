import React, { memo, useRef, useLayoutEffect } from 'react'
import { Input } from '@/components/ui/input'
import { Search } from 'lucide-react'

interface SearchInputProps {
  value: string
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  placeholder?: string
}

export const SearchInput = memo<SearchInputProps>(
  ({ value, onChange, placeholder = 'Search...' }) => {
    const inputRef = useRef<HTMLInputElement>(null)
    const isFocusedRef = useRef<boolean>(false)
    const lastCursorPositionRef = useRef<number>(0)
    const lastValueRef = useRef<string>(value)

    // Track focus state and cursor position more reliably
    useLayoutEffect(() => {
      const input = inputRef.current
      if (input && isFocusedRef.current) {
        // Only refocus if the value changed (indicating a state update)
        // and we're not dealing with the same component instance
        if (lastValueRef.current !== value) {
          input.focus()
          // Restore cursor position to the end or last known position
          const cursorPos = Math.min(
            lastCursorPositionRef.current,
            value.length
          )
          input.setSelectionRange(cursorPos, cursorPos)
        }
      }
      lastValueRef.current = value
    })

    const handleFocus = (e: React.FocusEvent<HTMLInputElement>) => {
      isFocusedRef.current = true
      lastCursorPositionRef.current = e.target.selectionStart || 0
    }

    const handleBlur = () => {
      isFocusedRef.current = false
    }

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      lastCursorPositionRef.current = e.target.selectionStart || 0
      onChange(e)
    }

    return (
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          ref={inputRef}
          placeholder={placeholder}
          value={value}
          onChange={handleChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          className="pl-10"
          // Add a unique key to prevent React from recreating the element
          key="search-input-stable"
        />
      </div>
    )
  }
)

SearchInput.displayName = 'SearchInput'
