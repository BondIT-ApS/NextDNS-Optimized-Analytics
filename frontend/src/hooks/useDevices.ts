import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/services/api'
import type { DeviceUsageItem } from '@/types/api'

export function useDevices(profile?: string, timeRange: string = '24h') {
  return useQuery({
    queryKey: ['devices', profile, timeRange],
    queryFn: () => apiClient.getDevices(profile, timeRange),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    enabled: true, // Always enabled, but will return empty list if no profile
  })
}

// Helper to get just the device names for filtering
export function useDeviceNames(profile?: string, timeRange: string = '24h') {
  const { data, ...rest } = useDevices(profile, timeRange)

  const deviceNames =
    data?.devices?.map((device: DeviceUsageItem) => device.device_name) || []

  return {
    deviceNames,
    devicesData: data,
    ...rest,
  }
}
