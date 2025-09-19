interface CacheEntry<T> {
  data: T
  timestamp: number
  ttl: number // Time to live in milliseconds
  queryKey: string
}

interface CacheMetadata {
  isOffline: boolean
  lastUpdated: number
  cacheHit: boolean
}

export class ApiCache {
  private static readonly STORAGE_PREFIX = 'nextdns-cache-'
  private static readonly DEFAULT_TTL = 5 * 60 * 1000 // 5 minutes
  private static readonly MAX_CACHE_SIZE = 50 // Maximum number of cache entries

  /**
   * Store data in cache with TTL
   */
  static set<T>(queryKey: string, data: T, ttl: number = this.DEFAULT_TTL): void {
    try {
      const cacheEntry: CacheEntry<T> = {
        data,
        timestamp: Date.now(),
        ttl,
        queryKey
      }

      const storageKey = this.STORAGE_PREFIX + queryKey
      localStorage.setItem(storageKey, JSON.stringify(cacheEntry))

      // Clean up old cache entries if we exceed max size
      this.cleanupCache()
    } catch (error) {
      console.warn('Failed to cache data:', error)
    }
  }

  /**
   * Get data from cache if still valid
   */
  static get<T>(queryKey: string): { data: T; metadata: CacheMetadata } | null {
    try {
      const storageKey = this.STORAGE_PREFIX + queryKey
      const cached = localStorage.getItem(storageKey)

      if (!cached) {
        return null
      }

      const cacheEntry: CacheEntry<T> = JSON.parse(cached)
      const now = Date.now()
      const age = now - cacheEntry.timestamp

      // Check if cache is expired
      if (age > cacheEntry.ttl) {
        // Remove expired cache
        localStorage.removeItem(storageKey)
        return null
      }

      return {
        data: cacheEntry.data,
        metadata: {
          isOffline: false, // Will be set by the caller
          lastUpdated: cacheEntry.timestamp,
          cacheHit: true
        }
      }
    } catch (error) {
      console.warn('Failed to retrieve cached data:', error)
      return null
    }
  }

  /**
   * Get data from cache even if expired (for offline fallback)
   */
  static getOffline<T>(queryKey: string): { data: T; metadata: CacheMetadata } | null {
    try {
      const storageKey = this.STORAGE_PREFIX + queryKey
      const cached = localStorage.getItem(storageKey)

      if (!cached) {
        return null
      }

      const cacheEntry: CacheEntry<T> = JSON.parse(cached)

      return {
        data: cacheEntry.data,
        metadata: {
          isOffline: true,
          lastUpdated: cacheEntry.timestamp,
          cacheHit: true
        }
      }
    } catch (error) {
      console.warn('Failed to retrieve offline cached data:', error)
      return null
    }
  }

  /**
   * Remove specific cache entry
   */
  static remove(queryKey: string): void {
    try {
      const storageKey = this.STORAGE_PREFIX + queryKey
      localStorage.removeItem(storageKey)
    } catch (error) {
      console.warn('Failed to remove cached data:', error)
    }
  }

  /**
   * Clear all cache entries
   */
  static clear(): void {
    try {
      Object.keys(localStorage)
        .filter(key => key.startsWith(this.STORAGE_PREFIX))
        .forEach(key => localStorage.removeItem(key))
    } catch (error) {
      console.warn('Failed to clear cache:', error)
    }
  }

  /**
   * Get cache statistics
   */
  static getStats(): {
    totalEntries: number
    totalSize: number
    oldestEntry: number | null
    newestEntry: number | null
  } {
    try {
      const cacheKeys = Object.keys(localStorage).filter(key => 
        key.startsWith(this.STORAGE_PREFIX)
      )

      let totalSize = 0
      let oldestEntry: number | null = null
      let newestEntry: number | null = null

      cacheKeys.forEach(key => {
        const cached = localStorage.getItem(key)
        if (cached) {
          totalSize += cached.length
          const cacheEntry = JSON.parse(cached)
          
          if (oldestEntry === null || cacheEntry.timestamp < oldestEntry) {
            oldestEntry = cacheEntry.timestamp
          }
          if (newestEntry === null || cacheEntry.timestamp > newestEntry) {
            newestEntry = cacheEntry.timestamp
          }
        }
      })

      return {
        totalEntries: cacheKeys.length,
        totalSize,
        oldestEntry,
        newestEntry
      }
    } catch (error) {
      console.warn('Failed to get cache stats:', error)
      return {
        totalEntries: 0,
        totalSize: 0,
        oldestEntry: null,
        newestEntry: null
      }
    }
  }

  /**
   * Clean up cache if it exceeds maximum size
   */
  private static cleanupCache(): void {
    try {
      const cacheKeys = Object.keys(localStorage)
        .filter(key => key.startsWith(this.STORAGE_PREFIX))

      if (cacheKeys.length <= this.MAX_CACHE_SIZE) {
        return
      }

      // Get all cache entries with timestamps
      const cacheEntries = cacheKeys
        .map(key => {
          const cached = localStorage.getItem(key)
          if (!cached) return null
          
          try {
            const entry = JSON.parse(cached)
            return { key, timestamp: entry.timestamp }
          } catch {
            return { key, timestamp: 0 }
          }
        })
        .filter(Boolean)
        .sort((a, b) => a!.timestamp - b!.timestamp) // Sort oldest first

      // Remove oldest entries to get back to max size
      const toRemove = cacheEntries.length - this.MAX_CACHE_SIZE
      for (let i = 0; i < toRemove; i++) {
        localStorage.removeItem(cacheEntries[i]!.key)
      }
    } catch (error) {
      console.warn('Failed to cleanup cache:', error)
    }
  }

  /**
   * Format cache age for display
   */
  static formatAge(timestamp: number): string {
    const age = Date.now() - timestamp
    const minutes = Math.floor(age / 60000)
    const seconds = Math.floor((age % 60000) / 1000)

    if (minutes > 60) {
      const hours = Math.floor(minutes / 60)
      const remainingMinutes = minutes % 60
      return `${hours}h ${remainingMinutes}m ago`
    } else if (minutes > 0) {
      return `${minutes}m ${seconds}s ago`
    } else {
      return `${seconds}s ago`
    }
  }

  /**
   * Check if we're likely offline based on recent failures
   */
  static isLikelyOffline(): boolean {
    // Simple heuristic: if we have no recent successful cache entries, we might be offline
    const stats = this.getStats()
    if (stats.totalEntries === 0) return false
    
    const recentThreshold = Date.now() - (2 * 60 * 1000) // 2 minutes
    return stats.newestEntry ? stats.newestEntry < recentThreshold : false
  }
}