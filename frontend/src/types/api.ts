// DNS Log types matching the FastAPI backend
export interface DNSLog {
  id: number
  timestamp: string
  domain: string
  action: string
  device?: { [key: string]: any } | null
  client_ip?: string | null
  query_type: string
  blocked: boolean
  profile_id?: string | null
  data?: { [key: string]: any } | null
  created_at: string
}

export interface LogsResponse {
  data: DNSLog[]
  total_records: number
  returned_records: number
  excluded_domains?: string[] | null
}

export interface LogsStatsResponse {
  total: number
  blocked: number
  allowed: number
  blocked_percentage: number
  allowed_percentage: number
  profile_id?: string | null
}

export interface ProfileInfo {
  profile_id: string
  record_count: number
  last_activity?: string | null
}

export interface ProfileListResponse {
  profiles: ProfileInfo[]
  total_profiles: number
}

export interface NextDNSProfileInfo {
  id: string
  name: string
  fingerprint?: string | null
  created?: string | null
  updated?: string | null
  error?: string | null
}

export interface ProfileInfoResponse {
  profiles: { [key: string]: NextDNSProfileInfo }
  total_profiles: number
}

export interface StatsResponse {
  total_records: number
  message: string
}

export interface HealthResponse {
  status: string
  healthy: boolean
}

export interface SystemResources {
  cpu_percent: number
  memory_total: number
  memory_available: number
  memory_percent: number
  disk_total: number
  disk_used: number
  disk_percent: number
  uptime_seconds: number
}

export interface DetailedHealthResponse {
  status_api: string
  status_db: string
  healthy: boolean
  total_dns_records: number
  fetch_interval_minutes: number
  log_level: string
  system_resources: SystemResources
  server_info: {
    python_version: string
    platform: string
    cpu_count: number
    memory_total: string
    memory_available: string
    disk_usage: string
    uptime: string
    database_status: string
    database_version: string
    total_logs: number
    logs_today: number
    frontend_stack?: {
      framework: string
      build_tool: string
      language: string
      styling: string
      ui_library: string
      state_management: string
    }
  }
  timestamp: string
}

// Authentication types
export interface AuthCredentials {
  username: string
  password: string
}

export interface User {
  username: string
  authenticated: boolean
}

// Filter and pagination types
export interface LogFilters {
  exclude?: string[]
  limit?: number
  offset?: number
  search?: string
  startDate?: string
  endDate?: string
  blocked?: boolean
  deviceFilter?: string
  profile?: string
}

// Chart data types
export interface ChartDataPoint {
  timestamp: string
  value: number
  label?: string
}

export interface DomainStats {
  domain: string
  count: number
  blocked: number
  percentage: number
}

export interface DeviceStats {
  device_name: string
  device_id: string
  count: number
  percentage: number
}