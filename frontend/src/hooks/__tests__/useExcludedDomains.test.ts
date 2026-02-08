import { describe, it, expect, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useExcludedDomains } from '../useExcludedDomains'

// 🧱 useExcludedDomains Hook Tests
// Validates the shared domain exclusion state brick

describe('🧱 useExcludedDomains Hook', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  describe('Initialization', () => {
    it('should initialize with empty array when no localStorage data', () => {
      const { result } = renderHook(() => useExcludedDomains())
      const [excludedDomains] = result.current

      expect(excludedDomains).toEqual([])
    })

    it('should initialize from existing localStorage data', () => {
      localStorage.setItem(
        'excluded_domains',
        JSON.stringify(['*.apple.com', '*.google.com'])
      )

      const { result } = renderHook(() => useExcludedDomains())
      const [excludedDomains] = result.current

      expect(excludedDomains).toEqual(['*.apple.com', '*.google.com'])
    })

    it('should handle corrupted JSON in localStorage gracefully', () => {
      localStorage.setItem('excluded_domains', 'not-valid-json{{{')

      const { result } = renderHook(() => useExcludedDomains())
      const [excludedDomains] = result.current

      expect(excludedDomains).toEqual([])
    })

    it('should handle non-array value in localStorage gracefully', () => {
      localStorage.setItem('excluded_domains', JSON.stringify('just-a-string'))

      const { result } = renderHook(() => useExcludedDomains())
      const [excludedDomains] = result.current

      expect(excludedDomains).toEqual([])
    })
  })

  describe('Persistence', () => {
    it('should persist changes to localStorage', () => {
      const { result } = renderHook(() => useExcludedDomains())

      act(() => {
        const [, setExcludedDomains] = result.current
        setExcludedDomains(['*.facebook.com', '*.meta.com'])
      })

      const stored = JSON.parse(
        localStorage.getItem('excluded_domains') || '[]'
      )
      expect(stored).toEqual(['*.facebook.com', '*.meta.com'])
    })

    it('should support functional updates', () => {
      localStorage.setItem('excluded_domains', JSON.stringify(['*.apple.com']))

      const { result } = renderHook(() => useExcludedDomains())

      act(() => {
        const [, setExcludedDomains] = result.current
        setExcludedDomains(prev => [...prev, '*.google.com'])
      })

      const [excludedDomains] = result.current
      expect(excludedDomains).toEqual(['*.apple.com', '*.google.com'])
    })
  })

  describe('Cross-tab Sync', () => {
    it('should update state when storage event fires for excluded_domains key', () => {
      const { result } = renderHook(() => useExcludedDomains())

      act(() => {
        window.dispatchEvent(
          new StorageEvent('storage', {
            key: 'excluded_domains',
            newValue: JSON.stringify(['*.netflix.com', '*.nflxvideo.net']),
          })
        )
      })

      const [excludedDomains] = result.current
      expect(excludedDomains).toEqual(['*.netflix.com', '*.nflxvideo.net'])
    })

    it('should ignore storage events for unrelated keys', () => {
      localStorage.setItem('excluded_domains', JSON.stringify(['*.apple.com']))
      const { result } = renderHook(() => useExcludedDomains())

      act(() => {
        window.dispatchEvent(
          new StorageEvent('storage', {
            key: 'some_other_key',
            newValue: JSON.stringify(['should-not-appear']),
          })
        )
      })

      const [excludedDomains] = result.current
      expect(excludedDomains).toEqual(['*.apple.com'])
    })

    it('should ignore storage events with invalid JSON', () => {
      localStorage.setItem('excluded_domains', JSON.stringify(['*.apple.com']))
      const { result } = renderHook(() => useExcludedDomains())

      act(() => {
        window.dispatchEvent(
          new StorageEvent('storage', {
            key: 'excluded_domains',
            newValue: 'broken-json{{{',
          })
        )
      })

      const [excludedDomains] = result.current
      expect(excludedDomains).toEqual(['*.apple.com'])
    })
  })
})
