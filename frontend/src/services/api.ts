import axios, { AxiosError, AxiosResponse } from 'axios'
import type { 
  LogsResponse, 
  StatsResponse, 
  HealthResponse, 
  DetailedHealthResponse,
  LogFilters
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
  async getLogs(filters: LogFilters = {}): Promise<LogsResponse> {
    const params = new URLSearchParams()
    
    if (filters.exclude && filters.exclude.length > 0) {
      filters.exclude.forEach(domain => params.append('exclude', domain))
    }
    if (filters.limit) params.append('limit', filters.limit.toString())
    if (filters.offset) params.append('offset', filters.offset.toString())

    const response = await api.get(`/logs?${params.toString()}`)
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