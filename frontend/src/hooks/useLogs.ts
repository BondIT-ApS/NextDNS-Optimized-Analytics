import { useQuery } from '@tanstack/react-query'

export interface DNSLog {
  id: number
  timestamp: string
  domain: string
  action: string
  device?: {
    id: string
    name: string
    model?: string
  } | null
  client_ip: string
  query_type: string
  blocked: boolean
  profile_id?: string | null
  data: {
    timestamp: string
    domain: string
    root: string
    tracker?: string
    encrypted: boolean
    protocol: string
    clientIp: string
    client?: string
    device?: {
      id: string
      name: string
      model?: string
    }
    status: string
    reasons: Array<{
      id: string
      name: string
    }>
    matched?: string
  }
  created_at: string
}

interface LogsResponse {
  data: DNSLog[]
  meta?: {
    total: number
    page: number
    limit: number
  }
}

const API_BASE_URL = 'http://localhost:5002/api'

interface LogsParams {
  limit?: number
  search?: string
  status?: 'all' | 'blocked' | 'allowed'
}

interface LogsStats {
  total: number
  blocked: number
  allowed: number
  blocked_percentage: number
  allowed_percentage: number
}

async function fetchLogs(params: LogsParams = {}): Promise<LogsResponse> {
  const { limit = 100, search = '', status = 'all' } = params
  const searchParams = new URLSearchParams({
    limit: limit.toString()
  })
  
  if (search.trim()) {
    searchParams.append('search', search)
  }
  
  if (status !== 'all') {
    searchParams.append('status', status)
  }
  
  const response = await fetch(`${API_BASE_URL}/logs?${searchParams}`)
  
  if (!response.ok) {
    throw new Error(`Failed to fetch logs: ${response.status} ${response.statusText}`)
  }
  
  return response.json()
}

async function fetchLogsStats(): Promise<LogsStats> {
  const response = await fetch(`${API_BASE_URL}/logs/stats`)
  
  if (!response.ok) {
    throw new Error(`Failed to fetch logs stats: ${response.status} ${response.statusText}`)
  }
  
  return response.json()
}

export function useLogs(params: LogsParams = {}) {
  return useQuery({
    queryKey: ['logs', params],
    queryFn: () => fetchLogs(params),
    staleTime: 30000, // 30 seconds
    refetchInterval: params.search || params.status !== 'all' ? false : 60000, // Only auto-refresh when no filters
  })
}

export function useLogsStats() {
  return useQuery({
    queryKey: ['logs-stats'],
    queryFn: fetchLogsStats,
    staleTime: 60000, // 60 seconds
    refetchInterval: 120000, // Refetch every 2 minutes
  })
}
