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

export interface BackendResources {
  cpu_percent: number
  memory_total: number
  memory_available: number
  memory_percent: number
  disk_total: number
  disk_used: number
  disk_percent: number
  uptime_seconds: number
}

export interface BackendStack {
  platform: string
  platform_release: string
  architecture: string
  hostname: string
  python_version: string
  cpu_count: number
  cpu_count_logical: number
}

export interface FrontendStack {
  framework: string
  build_tool: string
  language: string
  styling: string
  ui_library: string
  state_management: string
}

export interface BackendHealth {
  status: string
  uptime_seconds: number
}

export interface BackendMetrics {
  resources: BackendResources
  health: BackendHealth
}

export interface ConnectionStats {
  active: number
  total: number
  max_connections?: number
  usage_percent: number
}

export interface PerformanceMetrics {
  cache_hit_ratio: number
  database_size_mb: number
  total_queries: number
}

export interface DatabaseHealth {
  status: string
  uptime_seconds: number
}

export interface DatabaseMetrics {
  connections: ConnectionStats
  performance: PerformanceMetrics
  health: DatabaseHealth
}

export interface DetailedHealthResponse {
  status_api: string
  status_db: string
  healthy: boolean
  total_dns_records: number
  fetch_interval_minutes: number
  log_level: string
  backend_metrics: BackendMetrics
  backend_stack: BackendStack
  database_metrics?: DatabaseMetrics
  frontend_stack: FrontendStack
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
  devices?: string[]
  profile?: string
  time_range?: string
  status?: string
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

export interface DeviceUsageItem {
  device_name: string
  total_queries: number
  blocked_queries: number
  allowed_queries: number
  blocked_percentage: number
  allowed_percentage: number
  last_activity: string
}

export interface DeviceStatsResponse {
  devices: DeviceUsageItem[]
}

export interface DeviceStats {
  device_name: string
  device_id: string
  count: number
  percentage: number
}
