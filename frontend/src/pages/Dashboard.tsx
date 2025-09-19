import { useDetailedHealth, useStats } from '@/hooks/useApi'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { 
  Activity, 
  Database, 
  Server, 
  Clock,
  Cpu,
  HardDrive,
  MemoryStick,
  RefreshCw
} from 'lucide-react'
import { formatBytes, formatNumber } from '@/lib/utils'

export function Dashboard() {
  const { data: health, isLoading: healthLoading, refetch: refetchHealth } = useDetailedHealth()
  const { data: stats, isLoading: statsLoading } = useStats()

  if (healthLoading || statsLoading) {
    return (
      <div className="space-y-6">
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-6">
                <div className="h-4 bg-muted rounded w-3/4 mb-2"></div>
                <div className="h-8 bg-muted rounded w-1/2"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  const systemResources = health?.system_resources

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
          <p className="text-muted-foreground">System overview and analytics</p>
        </div>
        <Button 
          variant="outline" 
          onClick={() => refetchHealth()}
          disabled={healthLoading}
        >
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">DNS Records</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-lego-blue">
              {stats ? formatNumber(stats.total_records) : '0'}
            </div>
            <p className="text-xs text-muted-foreground">
              Total DNS log entries
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Health</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${health?.healthy ? 'text-lego-green' : 'text-lego-red'}`}>
              {health?.healthy ? 'Healthy' : 'Issues'}
            </div>
            <p className="text-xs text-muted-foreground">
              API & Database status
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Fetch Interval</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-lego-yellow">
              {health?.fetch_interval_minutes || 60}m
            </div>
            <p className="text-xs text-muted-foreground">
              Data refresh frequency
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Log Level</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-lego-orange">
              {health?.log_level || 'INFO'}
            </div>
            <p className="text-xs text-muted-foreground">
              Current logging level
            </p>
          </CardContent>
        </Card>
      </div>

      {/* System Resources */}
      {systemResources && (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
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
                  <span className="text-sm text-muted-foreground">Current</span>
                  <span className="text-sm font-medium">{systemResources.cpu_percent.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-secondary rounded-full h-2">
                  <div 
                    className="bg-lego-blue h-2 rounded-full transition-all duration-300"
                    style={{ width: `${Math.min(systemResources.cpu_percent, 100)}%` }}
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
                  <span className="text-sm text-muted-foreground">Used</span>
                  <span className="text-sm font-medium">
                    {formatBytes(systemResources.memory_total - systemResources.memory_available)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Total</span>
                  <span className="text-sm font-medium">
                    {formatBytes(systemResources.memory_total)}
                  </span>
                </div>
                <div className="w-full bg-secondary rounded-full h-2">
                  <div 
                    className="bg-lego-green h-2 rounded-full transition-all duration-300"
                    style={{ width: `${Math.min(systemResources.memory_percent, 100)}%` }}
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
                  <span className="text-sm text-muted-foreground">Used</span>
                  <span className="text-sm font-medium">
                    {formatBytes(systemResources.disk_used)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Total</span>
                  <span className="text-sm font-medium">
                    {formatBytes(systemResources.disk_total)}
                  </span>
                </div>
                <div className="w-full bg-secondary rounded-full h-2">
                  <div 
                    className="bg-lego-yellow h-2 rounded-full transition-all duration-300"
                    style={{ width: `${Math.min(systemResources.disk_percent, 100)}%` }}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* System Information */}
      {health && (
        <Card>
          <CardHeader>
            <CardTitle>System Information</CardTitle>
            <CardDescription>Server details and runtime information</CardDescription>
          </CardHeader>
          <CardContent>
            {/* Backend Stack Information */}
            <div>
              <h3 className="text-lg font-semibold mb-4 text-lego-blue">Backend Stack</h3>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                <div>
                  <h4 className="font-medium text-sm text-muted-foreground">Platform</h4>
                  <p className="font-mono text-sm">{health.server_info?.platform || 'Unknown'}</p>
                </div>
                <div>
                  <h4 className="font-medium text-sm text-muted-foreground">Python Version</h4>
                  <p className="font-mono text-sm">{health.server_info?.python_version || 'Unknown'}</p>
                </div>
                <div>
                  <h4 className="font-medium text-sm text-muted-foreground">CPU Cores</h4>
                  <p className="font-mono text-sm">{health.server_info?.cpu_count || 'Unknown'}</p>
                </div>
                <div>
                  <h4 className="font-medium text-sm text-muted-foreground">Uptime</h4>
                  <p className="font-mono text-sm">
                    {systemResources ? 
                      `${Math.floor(systemResources.uptime_seconds / 3600)}h ${Math.floor((systemResources.uptime_seconds % 3600) / 60)}m` 
                      : 'Unknown'
                    }
                  </p>
                </div>
                <div>
                  <h4 className="font-medium text-sm text-muted-foreground">Last Updated</h4>
                  <p className="font-mono text-sm">
                    {health.timestamp ? new Date(health.timestamp).toLocaleString() : 'Unknown'}
                  </p>
                </div>
              </div>
            </div>
            
            {/* Frontend Stack Information */}
            {health.server_info?.frontend_stack && (
              <div className="mt-6">
                <h3 className="text-lg font-semibold mb-4 text-lego-blue">Frontend Stack</h3>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  <div>
                    <h4 className="font-medium text-sm text-muted-foreground">Framework</h4>
                    <p className="font-mono text-sm">{health.server_info.frontend_stack.framework}</p>
                  </div>
                  <div>
                    <h4 className="font-medium text-sm text-muted-foreground">Build Tool</h4>
                    <p className="font-mono text-sm">{health.server_info.frontend_stack.build_tool}</p>
                  </div>
                  <div>
                    <h4 className="font-medium text-sm text-muted-foreground">Language</h4>
                    <p className="font-mono text-sm">{health.server_info.frontend_stack.language}</p>
                  </div>
                  <div>
                    <h4 className="font-medium text-sm text-muted-foreground">Styling</h4>
                    <p className="font-mono text-sm">{health.server_info.frontend_stack.styling}</p>
                  </div>
                  <div>
                    <h4 className="font-medium text-sm text-muted-foreground">UI Library</h4>
                    <p className="font-mono text-sm">{health.server_info.frontend_stack.ui_library}</p>
                  </div>
                  <div>
                    <h4 className="font-medium text-sm text-muted-foreground">State Management</h4>
                    <p className="font-mono text-sm">{health.server_info.frontend_stack.state_management}</p>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}