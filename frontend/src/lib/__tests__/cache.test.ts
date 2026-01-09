import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { ApiCache } from '../cache'

describe('🧱 ApiCache', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear()
    vi.clearAllMocks()
  })

  afterEach(() => {
    // Clean up after each test
    localStorage.clear()
  })

  describe('set and get', () => {
    it('should store and retrieve data from cache', () => {
      const testData = { id: 1, name: 'Test' }
      const queryKey = 'test-key'

      ApiCache.set(queryKey, testData)
      const result = ApiCache.get<typeof testData>(queryKey)

      expect(result).not.toBeNull()
      expect(result?.data).toEqual(testData)
      expect(result?.metadata.cacheHit).toBe(true)
      expect(result?.metadata.isOffline).toBe(false)
    })

    it('should return null for non-existent cache key', () => {
      const result = ApiCache.get('non-existent-key')
      expect(result).toBeNull()
    })

    it('should use custom TTL when provided', () => {
      const testData = { value: 42 }
      const queryKey = 'ttl-test'
      const customTTL = 10000 // 10 seconds

      ApiCache.set(queryKey, testData, customTTL)
      const result = ApiCache.get<typeof testData>(queryKey)

      expect(result).not.toBeNull()
      expect(result?.data).toEqual(testData)
    })

    it('should return null for expired cache entries', () => {
      const testData = { expired: true }
      const queryKey = 'expired-key'
      const shortTTL = 100 // 100ms

      // Use fake timers
      vi.useFakeTimers()
      
      ApiCache.set(queryKey, testData, shortTTL)
      
      // Fast-forward time beyond TTL
      vi.advanceTimersByTime(200)
      
      const result = ApiCache.get<typeof testData>(queryKey)
      expect(result).toBeNull()

      vi.useRealTimers()
    })

  })

  describe('getOffline', () => {
    it('should retrieve expired cache data for offline mode', () => {
      const testData = { offline: true }
      const queryKey = 'offline-key'
      const shortTTL = 100

      vi.useFakeTimers()
      
      ApiCache.set(queryKey, testData, shortTTL)
      vi.advanceTimersByTime(200) // Expire the cache
      
      const result = ApiCache.getOffline<typeof testData>(queryKey)
      
      expect(result).not.toBeNull()
      expect(result?.data).toEqual(testData)
      expect(result?.metadata.isOffline).toBe(true)
      expect(result?.metadata.cacheHit).toBe(true)

      vi.useRealTimers()
    })

    it('should return null when no cached data exists', () => {
      const result = ApiCache.getOffline('no-data')
      expect(result).toBeNull()
    })

  })

  describe('remove', () => {
    it('should remove specific cache entry', () => {
      const testData = { remove: true }
      const queryKey = 'remove-key'

      ApiCache.set(queryKey, testData)
      expect(ApiCache.get(queryKey)).not.toBeNull()

      ApiCache.remove(queryKey)
      expect(ApiCache.get(queryKey)).toBeNull()
    })

  })

  describe('clear', () => {
    it('should clear all cache entries', () => {
      ApiCache.set('key1', { data: 1 })
      ApiCache.set('key2', { data: 2 })
      ApiCache.set('key3', { data: 3 })

      expect(ApiCache.get('key1')).not.toBeNull()
      expect(ApiCache.get('key2')).not.toBeNull()

      ApiCache.clear()

      expect(ApiCache.get('key1')).toBeNull()
      expect(ApiCache.get('key2')).toBeNull()
      expect(ApiCache.get('key3')).toBeNull()
    })

    it('should not clear non-cache localStorage items', () => {
      localStorage.setItem('user-setting', 'value')
      ApiCache.set('cache-key', { data: 'test' })

      ApiCache.clear()

      expect(localStorage.getItem('user-setting')).toBe('value')
      expect(ApiCache.get('cache-key')).toBeNull()
    })

  })

  describe('getStats', () => {
    it('should return correct cache statistics', () => {
      ApiCache.set('key1', { data: 1 })
      ApiCache.set('key2', { data: 2 })
      ApiCache.set('key3', { data: 3 })

      const stats = ApiCache.getStats()

      expect(stats.totalEntries).toBe(3)
      expect(stats.totalSize).toBeGreaterThan(0)
      expect(stats.oldestEntry).not.toBeNull()
      expect(stats.newestEntry).not.toBeNull()
      expect(stats.newestEntry).toBeGreaterThanOrEqual(stats.oldestEntry!)
    })

    it('should return zero stats for empty cache', () => {
      const stats = ApiCache.getStats()

      expect(stats.totalEntries).toBe(0)
      expect(stats.totalSize).toBe(0)
      expect(stats.oldestEntry).toBeNull()
      expect(stats.newestEntry).toBeNull()
    })

  })

  describe('cache size management', () => {
    it('should handle multiple cache entries', () => {
      // Add multiple entries
      for (let i = 0; i < 10; i++) {
        ApiCache.set(`key${i}`, { index: i })
      }

      const stats = ApiCache.getStats()
      expect(stats.totalEntries).toBe(10)

      // Verify we can retrieve them
      for (let i = 0; i < 10; i++) {
        const result = ApiCache.get<{ index: number }>(`key${i}`)
        expect(result?.data.index).toBe(i)
      }
    })
  })

  describe('cache metadata', () => {
    it('should include timestamp in metadata', () => {
      const testData = { test: 'metadata' }
      const queryKey = 'metadata-key'
      const beforeTime = Date.now()

      ApiCache.set(queryKey, testData)
      const result = ApiCache.get<typeof testData>(queryKey)

      const afterTime = Date.now()

      expect(result?.metadata.lastUpdated).toBeGreaterThanOrEqual(beforeTime)
      expect(result?.metadata.lastUpdated).toBeLessThanOrEqual(afterTime)
    })
  })
})
