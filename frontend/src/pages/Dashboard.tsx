import {
  useDetailedHealth,
  useStats,
  useGlobalConnectionStatus,
} from '@/hooks/useApi'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  Activity,
  Database,
  Server,
  Clock,
  Cpu,
  HardDrive,
  MemoryStick,
  RefreshCw,
  AlertTriangle,
} from 'lucide-react'
import { formatBytes, formatNumber } from '@/lib/utils'
import { ApiErrorBoundary } from '@/components/ErrorBoundary'
import {
  DashboardCardSkeleton,
  SystemResourceCardSkeleton,
  SystemInfoSkeleton,
  LoadingState,
  ErrorState,
  ConnectionIndicator,
  RetryIndicator,
  OfflineBanner,
  DataFreshnessIndicator,
} from '@/components/LoadingSkeletons'

export function Dashboard() {
  const {
    data: health,
    isLoading: healthLoading,
    error: healthError,
    refetch: refetchHealth,
    failureCount: healthRetries,
    isFromCache: healthFromCache,
    cacheMetadata: healthCacheMetadata,
  } = useDetailedHealth()

  const {
    data: stats,
    isLoading: statsLoading,
    error: statsError,
    failureCount: statsRetries,
    isFromCache: statsFromCache,
    cacheMetadata: statsCacheMetadata,
  } = useStats()

  const globalConnection = useGlobalConnectionStatus()

  // Show loading skeletons on initial load
  if (healthLoading || statsLoading) {
    return (
      <div className="space-y-6">
        {/* Header with connection status */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
            <p className="text-muted-foreground">
              System overview and analytics
            </p>
          </div>
          <Button variant="outline" disabled>
            <RefreshCw className="mr-2 h-4 w-4" />
            Loading...
          </Button>
        </div>

        {/* Loading skeletons */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <DashboardCardSkeleton key={i} />
          ))}
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <SystemResourceCardSkeleton key={i} />
          ))}
        </div>

        <SystemInfoSkeleton />

        <LoadingState message="Loading dashboard data..." className="mt-8" />
      </div>
    )
  }

  const systemResources = health?.backend_metrics?.resources
  const totalRetries = (healthRetries || 0) + (statsRetries || 0)
  const hasErrors = Boolean(healthError || statsError)
  const isOfflineMode = healthFromCache || statsFromCache
  const oldestCacheTimestamp = Math.min(
    healthCacheMetadata?.lastUpdated || Date.now(),
    statsCacheMetadata?.lastUpdated || Date.now()
  )

  return (
    <div className="space-y-6">
      {/* Enhanced Header with Connection Status */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
          <div className="flex items-center gap-4 mt-1">
            <p className="text-muted-foreground">
              System overview and analytics
            </p>
            {hasErrors && (
              <div className="flex items-center gap-1 text-lego-orange text-sm">
                <AlertTriangle className="h-4 w-4" />
                <span>Some data may be outdated</span>
              </div>
            )}
          </div>
        </div>

        {/* Refresh Button */}
        <Button
          variant="outline"
          onClick={() => {
            refetchHealth()
            // Note: stats will auto-refresh due to the global connection hook
          }}
          disabled={healthLoading || statsLoading}
        >
          <RefreshCw
            className={`mr-2 h-4 w-4 ${healthLoading || statsLoading ? 'animate-spin' : ''}`}
          />
          {healthLoading || statsLoading ? 'Refreshing...' : 'Refresh'}
        </Button>
      </div>

      {/* Connection Status Panel */}
      <Card className="border-muted">
        <CardContent className="py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <ConnectionIndicator
                isConnected={globalConnection.isConnected}
                isLoading={globalConnection.isLoading}
              />
              {totalRetries > 0 && (
                <RetryIndicator
                  isRetrying={healthLoading || statsLoading}
                  retryCount={totalRetries}
                  maxRetries={5}
                />
              )}
            </div>
            <div className="flex flex-col items-end gap-1">
              <div className="text-xs text-muted-foreground">
                Last checked:{' '}
                {health?.timestamp
                  ? new Date(health.timestamp).toLocaleTimeString()
                  : 'Never'}
              </div>
              <DataFreshnessIndicator
                isFromCache={isOfflineMode}
                lastUpdated={oldestCacheTimestamp}
                isLoading={healthLoading || statsLoading}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Offline Mode Banner */}
      <OfflineBanner
        isOffline={isOfflineMode}
        lastUpdated={oldestCacheTimestamp}
      />

      {/* Stats Cards with Error Boundaries */}
      <ApiErrorBoundary componentName="Statistics">
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {/* DNS Records Card */}
          <Card className={statsError ? 'border-lego-orange' : ''}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">DNS Records</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {statsError ? (
                <ErrorState
                  message="Unable to load DNS record count"
                  showRetryButton={false}
                  className="py-2"
                />
              ) : (
                <>
                  <div className="text-2xl font-bold text-lego-blue">
                    {stats ? formatNumber(stats.total_records) : '0'}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Total DNS log entries
                  </p>
                </>
              )}
            </CardContent>
          </Card>

          {/* System Health Card */}
          <Card className={healthError ? 'border-lego-orange' : ''}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                System Health
              </CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {healthError ? (
                <ErrorState
                  message="Unable to check system health"
                  showRetryButton={false}
                  className="py-2"
                />
              ) : (
                <>
                  <div
                    className={`text-2xl font-bold ${health?.healthy ? 'text-lego-green' : 'text-lego-red'}`}
                  >
                    {health?.healthy ? 'Healthy' : 'Issues'}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    API & Database status
                  </p>
                </>
              )}
            </CardContent>
          </Card>

          {/* Fetch Interval Card */}
          <Card className={healthError ? 'border-lego-orange' : ''}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Fetch Interval
              </CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {healthError ? (
                <ErrorState
                  message="Unable to load fetch interval"
                  showRetryButton={false}
                  className="py-2"
                />
              ) : (
                <>
                  <div className="text-2xl font-bold text-lego-yellow">
                    {health?.fetch_interval_minutes || 60}m
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Data refresh frequency
                  </p>
                </>
              )}
            </CardContent>
          </Card>

          {/* Log Level Card */}
          <Card className={healthError ? 'border-lego-orange' : ''}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Log Level</CardTitle>
              <Server className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {healthError ? (
                <ErrorState
                  message="Unable to load log level"
                  showRetryButton={false}
                  className="py-2"
                />
              ) : (
                <>
                  <div className="text-2xl font-bold text-lego-orange">
                    {health?.log_level || 'INFO'}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Current logging level
                  </p>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </ApiErrorBoundary>

      {/* Backend Metrics with Error Boundaries */}
      <ApiErrorBoundary componentName="Backend Metrics">
        {systemResources ? (
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold text-lego-purple mb-4">
                Backend Metrics
              </h3>
            </div>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Cpu className="h-5 w-5 text-lego-blue" />
                    CPU Usage
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">
                        Current
                      </span>
                      <span className="text-sm font-medium">
                        {systemResources.cpu_percent.toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-secondary rounded-full h-2">
                      <div
                        className="bg-lego-blue h-2 rounded-full transition-all duration-300"
                        style={{
                          width: `${Math.min(systemResources.cpu_percent, 100)}%`,
                        }}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MemoryStick className="h-5 w-5 text-lego-green" />
                    Memory Usage
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">
                        Used
                      </span>
                      <span className="text-sm font-medium">
                        {formatBytes(
                          systemResources.memory_total -
                            systemResources.memory_available
                        )}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">
                        Total
                      </span>
                      <span className="text-sm font-medium">
                        {formatBytes(systemResources.memory_total)}
                      </span>
                    </div>
                    <div className="w-full bg-secondary rounded-full h-2">
                      <div
                        className="bg-lego-green h-2 rounded-full transition-all duration-300"
                        style={{
                          width: `${Math.min(systemResources.memory_percent, 100)}%`,
                        }}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <HardDrive className="h-5 w-5 text-lego-yellow" />
                    Disk Usage
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">
                        Used
                      </span>
                      <span className="text-sm font-medium">
                        {formatBytes(systemResources.disk_used)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">
                        Total
                      </span>
                      <span className="text-sm font-medium">
                        {formatBytes(systemResources.disk_total)}
                      </span>
                    </div>
                    <div className="w-full bg-secondary rounded-full h-2">
                      <div
                        className="bg-lego-yellow h-2 rounded-full transition-all duration-300"
                        style={{
                          width: `${Math.min(systemResources.disk_percent, 100)}%`,
                        }}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Backend Health Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="h-5 w-5 text-lego-blue" />
                    Backend Health
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">
                        Status
                      </span>
                      <span
                        className={`text-sm font-medium ${
                          health?.backend_metrics?.health.status === 'healthy'
                            ? 'text-lego-green'
                            : health?.backend_metrics?.health.status ===
                                'warning'
                              ? 'text-lego-yellow'
                              : 'text-lego-red'
                        }`}
                      >
                        {health?.backend_metrics?.health.status
                          .charAt(0)
                          .toUpperCase() +
                          health?.backend_metrics?.health.status.slice(1) ||
                          'Unknown'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">
                        Uptime
                      </span>
                      <span className="text-sm font-medium">
                        {health?.backend_metrics?.health.uptime_seconds
                          ? `${Math.floor(health.backend_metrics.health.uptime_seconds / 3600)}h ${Math.floor((health.backend_metrics.health.uptime_seconds % 3600) / 60)}m`
                          : 'Unknown'}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        ) : healthError ? (
          <ErrorState
            message="Unable to load system resources"
            className="py-8"
          />
        ) : null}
      </ApiErrorBoundary>

      {/* Database Metrics with Error Boundaries */}
      <ApiErrorBoundary componentName="Database Metrics">
        {health?.database_metrics ? (
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold text-lego-purple mb-4">
                Database Metrics
              </h3>
            </div>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {/* Connection Statistics Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Database className="h-5 w-5 text-lego-purple" />
                    Connections
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">
                        Active
                      </span>
                      <span className="text-sm font-medium">
                        {health.database_metrics.connections.active}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">
                        Total
                      </span>
                      <span className="text-sm font-medium">
                        {health.database_metrics.connections.total}
                      </span>
                    </div>
                    <div className="w-full bg-secondary rounded-full h-2">
                      <div
                        className="bg-lego-purple h-2 rounded-full transition-all duration-300"
                        style={{
                          width: `${Math.min(health.database_metrics.connections.usage_percent, 100)}%`,
                        }}
                      />
                    </div>
                    <div className="text-xs text-muted-foreground text-center">
                      {health.database_metrics.connections.usage_percent.toFixed(
                        1
                      )}
                      % utilization
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Performance Metrics Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="h-5 w-5 text-lego-green" />
                    Performance
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">
                        Cache Hit
                      </span>
                      <span className="text-sm font-medium">
                        {(
                          health.database_metrics.performance.cache_hit_ratio *
                          100
                        ).toFixed(1)}
                        %
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">
                        DB Size
                      </span>
                      <span className="text-sm font-medium">
                        {health.database_metrics.performance.database_size_mb}MB
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">
                        Total Queries
                      </span>
                      <span className="text-sm font-medium">
                        {formatNumber(
                          health.database_metrics.performance.total_queries
                        )}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Database Health Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Server className="h-5 w-5 text-lego-blue" />
                    Database Health
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">
                        Status
                      </span>
                      <span
                        className={`text-sm font-medium ${
                          health.database_metrics.health.status === 'healthy'
                            ? 'text-lego-green'
                            : health.database_metrics.health.status ===
                                'warning'
                              ? 'text-lego-yellow'
                              : 'text-lego-red'
                        }`}
                      >
                        {health.database_metrics.health.status
                          .charAt(0)
                          .toUpperCase() +
                          health.database_metrics.health.status.slice(1)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">
                        Uptime
                      </span>
                      <span className="text-sm font-medium">
                        {Math.floor(
                          health.database_metrics.health.uptime_seconds / 3600
                        )}
                        h{' '}
                        {Math.floor(
                          (health.database_metrics.health.uptime_seconds %
                            3600) /
                            60
                        )}
                        m
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        ) : healthError ? (
          <ErrorState
            message="Unable to load backend metrics"
            className="py-8"
          />
        ) : null}
      </ApiErrorBoundary>

      {/* System Information with Error Boundaries */}
      <ApiErrorBoundary componentName="System Information">
        {health ? (
          <Card>
            <CardHeader>
              <CardTitle>System Information</CardTitle>
              <CardDescription>
                Server details and runtime information
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Backend Stack Information */}
              <div>
                <h3 className="text-lg font-semibold mb-4 text-lego-blue">
                  Backend Stack
                </h3>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  <div>
                    <h4 className="font-medium text-sm text-muted-foreground">
                      Platform
                    </h4>
                    <p className="font-mono text-sm">
                      {health.backend_stack?.platform || 'Unknown'}
                    </p>
                  </div>
                  <div>
                    <h4 className="font-medium text-sm text-muted-foreground">
                      Python Version
                    </h4>
                    <p className="font-mono text-sm">
                      {health.backend_stack?.python_version || 'Unknown'}
                    </p>
                  </div>
                  <div>
                    <h4 className="font-medium text-sm text-muted-foreground">
                      CPU Cores
                    </h4>
                    <p className="font-mono text-sm">
                      {health.backend_stack?.cpu_count || 'Unknown'}
                    </p>
                  </div>
                  <div>
                    <h4 className="font-medium text-sm text-muted-foreground">
                      Uptime
                    </h4>
                    <p className="font-mono text-sm">
                      {health?.backend_metrics?.health.uptime_seconds
                        ? `${Math.floor(health.backend_metrics.health.uptime_seconds / 3600)}h ${Math.floor((health.backend_metrics.health.uptime_seconds % 3600) / 60)}m`
                        : 'Unknown'}
                    </p>
                  </div>
                  <div>
                    <h4 className="font-medium text-sm text-muted-foreground">
                      Last Updated
                    </h4>
                    <p className="font-mono text-sm">
                      {health.timestamp
                        ? new Date(health.timestamp).toLocaleString()
                        : 'Unknown'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Frontend Stack Information */}
              {health.frontend_stack && (
                <div className="mt-6">
                  <h3 className="text-lg font-semibold mb-4 text-lego-blue">
                    Frontend Stack
                  </h3>
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    <div>
                      <h4 className="font-medium text-sm text-muted-foreground">
                        Framework
                      </h4>
                      <p className="font-mono text-sm">
                        {health.frontend_stack.framework}
                      </p>
                    </div>
                    <div>
                      <h4 className="font-medium text-sm text-muted-foreground">
                        Build Tool
                      </h4>
                      <p className="font-mono text-sm">
                        {health.frontend_stack.build_tool}
                      </p>
                    </div>
                    <div>
                      <h4 className="font-medium text-sm text-muted-foreground">
                        Language
                      </h4>
                      <p className="font-mono text-sm">
                        {health.frontend_stack.language}
                      </p>
                    </div>
                    <div>
                      <h4 className="font-medium text-sm text-muted-foreground">
                        Styling
                      </h4>
                      <p className="font-mono text-sm">
                        {health.frontend_stack.styling}
                      </p>
                    </div>
                    <div>
                      <h4 className="font-medium text-sm text-muted-foreground">
                        UI Library
                      </h4>
                      <p className="font-mono text-sm">
                        {health.frontend_stack.ui_library}
                      </p>
                    </div>
                    <div>
                      <h4 className="font-medium text-sm text-muted-foreground">
                        State Management
                      </h4>
                      <p className="font-mono text-sm">
                        {health.frontend_stack.state_management}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ) : healthError ? (
          <ErrorState
            message="Unable to load system information"
            className="py-8"
          />
        ) : null}
      </ApiErrorBoundary>
    </div>
  )
}
