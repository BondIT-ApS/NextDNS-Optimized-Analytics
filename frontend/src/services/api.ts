import axios, { AxiosError, AxiosResponse } from 'axios'
import type {
  LogsResponse,
  LogsStatsResponse,
  StatsResponse,
  HealthResponse,
  DetailedHealthResponse,
  ProfileListResponse,
  ProfileInfoResponse,
  NextDNSProfileInfo,
  DeviceStatsResponse,
  LogFilters,
} from '@/types/api'

// Create axios instance
const api = axios.create({
  baseURL: '/api',
  timeout: 5000, // 5 seconds for faster failure detection
  headers: {
    'Content-Type': 'application/json',
  },
})

// No auth needed - app is open for everyone
// API key is configured server-side for protected endpoints

// Response interceptor for error handling
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    return Promise.reject({
      message: error.message,
      status: error.response?.status,
      data: error.response?.data,
    })
  }
)

// API endpoints
export const apiClient = {
  // Health endpoints
  async getHealth(): Promise<HealthResponse> {
    const response = await api.get('/health')
    return response.data
  },

  async getDetailedHealth(): Promise<DetailedHealthResponse> {
    const response = await api.get('/health/detailed')
    return response.data
  },

  // Stats endpoint
  async getStats(): Promise<StatsResponse> {
    const response = await api.get('/stats')
    return response.data
  },

  // Logs endpoints
  async getLogs(
    filters: LogFilters & { status?: string } = {}
  ): Promise<LogsResponse> {
    const params = new URLSearchParams()

    if (filters.exclude && filters.exclude.length > 0) {
      filters.exclude.forEach(domain => params.append('exclude', domain))
    }
    if (filters.limit) params.append('limit', filters.limit.toString())
    if (filters.offset) params.append('offset', filters.offset.toString())
    if (filters.search) params.append('search', filters.search)
    if (filters.status && filters.status !== 'all')
      params.append('status', filters.status)
    if (filters.profile) params.append('profile', filters.profile)
    if (filters.devices && filters.devices.length > 0) {
      filters.devices.forEach(device => params.append('devices', device))
    }
    if (filters.time_range) params.append('time_range', filters.time_range)

    const response = await api.get(`/logs?${params.toString()}`)
    return response.data
  },

  async getLogsStats(profile?: string): Promise<LogsStatsResponse> {
    const params = new URLSearchParams()
    if (profile) params.append('profile', profile)

    const response = await api.get(`/logs/stats?${params.toString()}`)
    return response.data
  },

  // Profile endpoints
  async getAvailableProfiles(): Promise<ProfileListResponse> {
    const response = await api.get('/profiles')
    return response.data
  },

  async getProfilesInfo(): Promise<ProfileInfoResponse> {
    const response = await api.get('/profiles/info')
    return response.data
  },

  async getProfileInfo(profileId: string): Promise<NextDNSProfileInfo> {
    const response = await api.get(`/profiles/${profileId}/info`)
    return response.data
  },

  // Device endpoints
  async getDevices(
    profile?: string,
    timeRange: string = '24h'
  ): Promise<DeviceStatsResponse> {
    const params = new URLSearchParams()
    if (profile) params.append('profile', profile)
    params.append('time_range', timeRange)

    const response = await api.get(`/devices?${params.toString()}`)
    return response.data
  },

  // Device analytics endpoint
  async getDeviceStats(
    profile?: string,
    timeRange: string = '24h',
    limit: number = 10,
    exclude: string[] = []
  ): Promise<DeviceStatsResponse> {
    const params = new URLSearchParams()
    if (profile) params.append('profile', profile)
    params.append('time_range', timeRange)
    params.append('limit', limit.toString())
    if (exclude.length > 0) {
      exclude.forEach(device => params.append('exclude', device))
    }

    const response = await api.get(`/stats/devices?${params.toString()}`)
    return response.data
  },

  // Root endpoint
  async getRoot() {
    const response = await api.get('/')
    return response.data
  },

  // No authentication needed - app is open
}

export default api
