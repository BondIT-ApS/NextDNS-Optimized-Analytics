import { useState, useEffect, useCallback } from 'react'

const STORAGE_KEY = 'excluded_domains'

/**
 * Shared hook for managing domain exclusion patterns.
 * Persists to localStorage with a single shared key so exclusions
 * are consistent across all pages (Stats, Logs, etc.).
 *
 * Listens to storage events so changes in one tab are reflected in others.
 */
export function useExcludedDomains() {
  const [excludedDomains, setExcludedDomainsState] = useState<string[]>(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        return Array.isArray(parsed) ? parsed : []
      } catch {
        return []
      }
    }
    return []
  })

  // Persist to localStorage whenever the value changes
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(excludedDomains))
  }, [excludedDomains])

  // Listen for storage changes from other tabs/windows
  useEffect(() => {
    const handleStorage = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY && e.newValue) {
        try {
          const parsed = JSON.parse(e.newValue)
          if (Array.isArray(parsed)) {
            setExcludedDomainsState(parsed)
          }
        } catch {
          // ignore parse errors
        }
      }
    }

    window.addEventListener('storage', handleStorage)
    return () => window.removeEventListener('storage', handleStorage)
  }, [])

  const setExcludedDomains = useCallback((domains: string[] | ((prev: string[]) => string[])) => {
    setExcludedDomainsState(domains)
  }, [])

  return [excludedDomains, setExcludedDomains] as const
}
