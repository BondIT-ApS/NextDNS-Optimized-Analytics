import React, { useState, useCallback } from 'react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { X, PlusCircle, AlertCircle, HelpCircle } from 'lucide-react'

interface DomainExclusionInputProps {
  value: string[]
  onChange: (patterns: string[]) => void
  placeholder?: string
  className?: string
}

// Validate wildcard pattern
const validatePattern = (
  pattern: string
): {
  valid: boolean
  error?: string
} => {
  if (!pattern || !pattern.trim()) {
    return { valid: false, error: 'Pattern cannot be empty' }
  }

  const trimmed = pattern.trim()

  // Check for overly broad patterns
  if (trimmed === '*' || trimmed === '**' || trimmed === '*.*') {
    return {
      valid: false,
      error: 'Pattern too broad - please be more specific',
    }
  }

  // Check for valid domain characters
  const validPattern = /^[a-zA-Z0-9*.\-_]+$/
  if (!validPattern.test(trimmed)) {
    return {
      valid: false,
      error: 'Pattern contains invalid characters',
    }
  }

  // Check for consecutive wildcards
  if (trimmed.includes('**')) {
    return { valid: false, error: 'Consecutive wildcards not allowed' }
  }

  return { valid: true }
}

// Format pattern for display
const formatPattern = (pattern: string): string => {
  return pattern.trim().toLowerCase()
}

export const DomainExclusionInput: React.FC<DomainExclusionInputProps> = ({
  value,
  onChange,
  placeholder = 'Enter domain pattern (e.g., *.apple.com)',
  className = '',
}) => {
  const [inputValue, setInputValue] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [showHelp, setShowHelp] = useState(false)

  const handleAdd = useCallback(() => {
    const validation = validatePattern(inputValue)

    if (!validation.valid) {
      setError(validation.error || 'Invalid pattern')
      return
    }

    const formatted = formatPattern(inputValue)

    // Check for duplicates
    if (value.includes(formatted)) {
      setError('Pattern already exists')
      return
    }

    onChange([...value, formatted])
    setInputValue('')
    setError(null)
  }, [inputValue, value, onChange])

  const handleRemove = useCallback(
    (pattern: string) => {
      onChange(value.filter(p => p !== pattern))
    },
    [value, onChange]
  )

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') {
        e.preventDefault()
        handleAdd()
      } else if (e.key === 'Escape') {
        setInputValue('')
        setError(null)
      }
    },
    [handleAdd]
  )

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setInputValue(e.target.value)
      setError(null)
    },
    []
  )

  return (
    <div className={`space-y-2 ${className}`}>
      <div className="flex items-start gap-2">
        <div className="flex-1 space-y-1">
          <div className="flex items-center gap-2">
            <Input
              value={inputValue}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              className={error ? 'border-destructive' : ''}
              aria-invalid={!!error}
              aria-describedby={error ? 'pattern-error' : undefined}
            />
            <Button
              onClick={handleAdd}
              size="sm"
              variant="outline"
              disabled={!inputValue.trim()}
              title="Add pattern"
            >
              <PlusCircle className="h-4 w-4" />
            </Button>
            <Button
              onClick={() => setShowHelp(!showHelp)}
              size="sm"
              variant="ghost"
              title="Show pattern help"
            >
              <HelpCircle className="h-4 w-4" />
            </Button>
          </div>
          {error && (
            <div
              id="pattern-error"
              className="flex items-center gap-1 text-sm text-destructive"
            >
              <AlertCircle className="h-3 w-3" />
              <span>{error}</span>
            </div>
          )}
        </div>
      </div>

      {showHelp && (
        <div className="rounded-md bg-muted p-3 text-sm space-y-2">
          <p className="font-semibold">Wildcard Pattern Examples:</p>
          <ul className="list-disc list-inside space-y-1 text-muted-foreground">
            <li>
              <code className="bg-background px-1 rounded">*.apple.com</code> -
              Excludes all subdomains (icloud.apple.com, www.apple.com)
            </li>
            <li>
              <code className="bg-background px-1 rounded">tracking.*</code> -
              Excludes all TLDs (tracking.com, tracking.net)
            </li>
            <li>
              <code className="bg-background px-1 rounded">*analytics*</code> -
              Excludes domains containing "analytics"
            </li>
            <li>
              <code className="bg-background px-1 rounded">google.com</code> -
              Exact domain match (no wildcards)
            </li>
          </ul>
          <p className="text-xs text-muted-foreground mt-2">
            Press <kbd className="px-1 bg-background rounded">Enter</kbd> to add
            pattern, <kbd className="px-1 bg-background rounded">Esc</kbd> to
            clear
          </p>
        </div>
      )}

      {value.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {value.map(pattern => (
            <Badge
              key={pattern}
              variant="secondary"
              className="pl-2 pr-1 py-1 text-xs"
            >
              <span className="mr-1 font-mono">{pattern}</span>
              <button
                onClick={() => handleRemove(pattern)}
                className="ml-1 rounded-full hover:bg-background/50 transition-colors"
                title={`Remove ${pattern}`}
                aria-label={`Remove exclusion pattern ${pattern}`}
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}

      {value.length > 0 && (
        <p className="text-xs text-muted-foreground">
          {value.length} pattern{value.length !== 1 ? 's' : ''} active
        </p>
      )}
    </div>
  )
}

DomainExclusionInput.displayName = 'DomainExclusionInput'
