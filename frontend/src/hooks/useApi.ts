import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/services/api'
import type { LogFilters } from '@/types/api'

// Query keys
export const queryKeys = {
  health: ['health'] as const,
  healthDetailed: ['health', 'detailed'] as const,
  stats: ['stats'] as const,
  logs: (filters: LogFilters) => ['logs', filters] as const,
  root: ['root'] as const,
}

// Health hooks
export const useHealth = () => {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: () => apiClient.getHealth(),
    refetchInterval: 30000, // Refetch every 30 seconds
    staleTime: 15000, // Consider data fresh for 15 seconds
  })
}

export const useDetailedHealth = () => {
  return useQuery({
    queryKey: queryKeys.healthDetailed,
    queryFn: () => apiClient.getDetailedHealth(),
    refetchInterval: 60000, // Refetch every minute
    staleTime: 30000, // Consider data fresh for 30 seconds
  })
}

// Stats hook
export const useStats = () => {
  return useQuery({
    queryKey: queryKeys.stats,
    queryFn: () => apiClient.getStats(),
    refetchInterval: 30000,
    staleTime: 15000,
    retry: (failureCount, error: any) => {
      // Don't retry on auth errors
      if (error.status === 401) return false
      return failureCount < 3
    }
  })
}

// Logs hook with filtering and pagination
export const useLogs = (filters: LogFilters = {}) => {
  return useQuery({
    queryKey: queryKeys.logs(filters),
    queryFn: () => apiClient.getLogs(filters),
    refetchInterval: 60000, // Refetch every minute for real-time updates
    staleTime: 30000,
    placeholderData: (prev) => prev, // Keep previous data while fetching new
    retry: (failureCount, error: any) => {
      if (error.status === 401) return false
      return failureCount < 3
    }
  })
}

// Root endpoint hook
export const useRoot = () => {
  return useQuery({
    queryKey: queryKeys.root,
    queryFn: () => apiClient.getRoot(),
    staleTime: 300000, // 5 minutes - this data doesn't change often
  })
}

// No authentication needed - app is open for everyone

// Custom hook for real-time log updates
export const useRealtimeLogs = (filters: LogFilters = {}, enabled = true) => {
  return useQuery({
    queryKey: [...queryKeys.logs(filters), 'realtime'],
    queryFn: () => apiClient.getLogs(filters),
    refetchInterval: enabled ? 15000 : false, // Refresh every 15 seconds when enabled
    enabled,
    retry: (failureCount, error: any) => {
      if (error.status === 401) return false
      return failureCount < 2
    }
  })
}