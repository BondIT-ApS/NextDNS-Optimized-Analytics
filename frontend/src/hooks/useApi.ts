import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/services/api'
import type { LogFilters } from '@/types/api'
import { ApiCache } from '@/lib/cache'

// Enhanced retry configuration with exponential backoff and caching
const createRetryConfig = (
  maxRetries: number = 3,
  queryKey?: readonly string[]
) => {
  return {
    retry: (failureCount: number, error: any) => {
      // Don't retry on auth errors (401) or client errors (400-499)
      if (error?.status >= 400 && error?.status < 500) return false
      return failureCount < maxRetries
    },
    retryDelay: (attemptIndex: number) => {
      // Exponential backoff: 1s, 2s, 4s, 8s...
      return Math.min(1000 * 2 ** attemptIndex, 30000)
    },
    // Handle failed queries by falling back to cache
    onError: (error: any) => {
      console.warn(`API Error for ${queryKey?.join('-')}:`, error)
    },
  }
}

// Enhanced connection status helper with offline detection
const getConnectionStatus = (
  error: any,
  isLoading: boolean,
  data: any,
  isFromCache: boolean = false
) => {
  if (isLoading && !isFromCache) return { isConnected: false, isLoading: true }
  if (error && !isFromCache) return { isConnected: false, isLoading: false }
  return {
    isConnected: Boolean(data) && !isFromCache,
    isLoading: false,
    isOffline: isFromCache,
  }
}

// Cache-aware query function wrapper
const createCacheAwareQuery = <T>(
  queryFn: () => Promise<T>,
  queryKey: readonly string[],
  ttl?: number
) => {
  return async (): Promise<T & { _cacheMetadata?: any }> => {
    const cacheKey = queryKey.join('-')

    try {
      // Try to fetch fresh data
      const data = await queryFn()

      // Cache successful response
      ApiCache.set(cacheKey, data, ttl)

      return data as T & { _cacheMetadata?: any }
    } catch (error) {
      // On error, try to get cached data (even if expired)
      const cached = ApiCache.getOffline<T>(cacheKey)

      if (cached) {
        console.info(`Using offline cache for ${cacheKey}:`, {
          age: ApiCache.formatAge(cached.metadata.lastUpdated),
          isOffline: cached.metadata.isOffline,
        })

        // Return cached data with metadata
        return {
          ...cached.data,
          _cacheMetadata: cached.metadata,
        } as T & { _cacheMetadata?: any }
      }

      // If no cache available, re-throw the error
      throw error
    }
  }
}

// Query keys
export const queryKeys = {
  health: ['health'] as const,
  healthDetailed: ['health', 'detailed'] as const,
  stats: ['stats'] as const,
  logs: (filters: LogFilters) => ['logs', filters] as const,
  root: ['root'] as const,
}

// Health hooks with enhanced error handling and caching
export const useHealth = () => {
  const query = useQuery({
    queryKey: queryKeys.health,
    queryFn: createCacheAwareQuery(
      () => apiClient.getHealth(),
      queryKeys.health,
      30000 // 30 second cache TTL
    ),
    refetchInterval: 30000, // Refetch every 30 seconds
    staleTime: 15000, // Consider data fresh for 15 seconds
    ...createRetryConfig(5, queryKeys.health), // Allow more retries for health checks
  })

  const isFromCache = Boolean(query.data?._cacheMetadata?.isOffline)

  return {
    ...query,
    connectionStatus: getConnectionStatus(
      query.error,
      query.isLoading,
      query.data,
      isFromCache
    ),
    isFromCache,
    cacheMetadata: query.data?._cacheMetadata,
  }
}

export const useDetailedHealth = () => {
  const query = useQuery({
    queryKey: queryKeys.healthDetailed,
    queryFn: createCacheAwareQuery(
      () => apiClient.getDetailedHealth(),
      queryKeys.healthDetailed,
      60000 // 1 minute cache TTL
    ),
    refetchInterval: 60000, // Refetch every minute
    staleTime: 30000, // Consider data fresh for 30 seconds
    ...createRetryConfig(5, queryKeys.healthDetailed), // Allow more retries for health checks
    refetchOnWindowFocus: true, // Refetch when user returns to tab
  })

  const isFromCache = Boolean(query.data?._cacheMetadata?.isOffline)

  return {
    ...query,
    connectionStatus: getConnectionStatus(
      query.error,
      query.isLoading,
      query.data,
      isFromCache
    ),
    isFromCache,
    cacheMetadata: query.data?._cacheMetadata,
  }
}

// Stats hook with enhanced retry logic and caching
export const useStats = () => {
  const query = useQuery({
    queryKey: queryKeys.stats,
    queryFn: createCacheAwareQuery(
      () => apiClient.getStats(),
      queryKeys.stats,
      30000 // 30 second cache TTL
    ),
    refetchInterval: 30000,
    staleTime: 15000,
    ...createRetryConfig(3, queryKeys.stats),
  })

  const isFromCache = Boolean(query.data?._cacheMetadata?.isOffline)

  return {
    ...query,
    connectionStatus: getConnectionStatus(
      query.error,
      query.isLoading,
      query.data,
      isFromCache
    ),
    isFromCache,
    cacheMetadata: query.data?._cacheMetadata,
  }
}

// Logs hook with filtering, pagination, and enhanced retry logic
export const useLogs = (filters: LogFilters = {}) => {
  const query = useQuery({
    queryKey: queryKeys.logs(filters),
    queryFn: () => apiClient.getLogs(filters),
    refetchInterval: 60000, // Refetch every minute for real-time updates
    staleTime: 30000,
    placeholderData: prev => prev, // Keep previous data while fetching new
    ...createRetryConfig(3),
  })

  return {
    ...query,
    connectionStatus: getConnectionStatus(
      query.error,
      query.isLoading,
      query.data
    ),
  }
}

// Root endpoint hook
export const useRoot = () => {
  const query = useQuery({
    queryKey: queryKeys.root,
    queryFn: () => apiClient.getRoot(),
    staleTime: 300000, // 5 minutes - this data doesn't change often
    ...createRetryConfig(2), // Less retries for root endpoint
  })

  return {
    ...query,
    connectionStatus: getConnectionStatus(
      query.error,
      query.isLoading,
      query.data
    ),
  }
}

// Custom hook for real-time log updates with enhanced error handling
export const useRealtimeLogs = (filters: LogFilters = {}, enabled = true) => {
  const query = useQuery({
    queryKey: [...queryKeys.logs(filters), 'realtime'],
    queryFn: () => apiClient.getLogs(filters),
    refetchInterval: enabled ? 15000 : false, // Refresh every 15 seconds when enabled
    enabled,
    ...createRetryConfig(2), // Less aggressive retries for realtime updates
  })

  return {
    ...query,
    connectionStatus: getConnectionStatus(
      query.error,
      query.isLoading,
      query.data
    ),
  }
}

// Global connection status hook - combines multiple health checks
export const useGlobalConnectionStatus = () => {
  const health = useHealth()
  const detailedHealth = useDetailedHealth()

  // Determine overall connection status
  const isConnected = Boolean(
    (health.data || detailedHealth.data) &&
      !health.error &&
      !detailedHealth.error
  )

  const isLoading = health.isLoading || detailedHealth.isLoading

  // Count retry attempts across all queries
  const totalRetries =
    (health.failureCount || 0) + (detailedHealth.failureCount || 0)

  return {
    isConnected,
    isLoading,
    totalRetries,
    lastError: health.error || detailedHealth.error,
    healthData: health.data,
    detailedHealthData: detailedHealth.data,
  }
}
