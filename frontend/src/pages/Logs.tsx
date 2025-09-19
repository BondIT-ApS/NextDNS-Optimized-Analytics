import { useLogs } from '@/hooks/useApi'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  RefreshCw, 
  Search,
  Database,
  Shield,
  Clock,
  CheckCircle,
  XCircle
} from 'lucide-react'
import { formatNumber } from '@/lib/utils'
import { ApiErrorBoundary } from '@/components/ErrorBoundary'
import { LoadingState, ErrorState } from '@/components/LoadingSkeletons'
import { useState, useMemo } from 'react'

export function Logs() {
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'blocked' | 'allowed'>('all')
  
  const { 
    data: logsResponse, 
    isLoading, 
    error, 
    refetch 
  } = useLogs({ limit: 100 }) // Get last 100 logs

  // Filter logs based on search and status
  const filteredLogs = useMemo(() => {
    if (!logsResponse?.data) return []
    
    let filtered = logsResponse.data
    
    // Filter by search query (domain name)
    if (searchQuery.trim()) {
      filtered = filtered.filter(log => 
        log.domain.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }
    
    // Filter by status
    if (statusFilter !== 'all') {
      filtered = filtered.filter(log => 
        statusFilter === 'blocked' ? log.blocked : !log.blocked
      )
    }
    
    return filtered
  }, [logsResponse?.data, searchQuery, statusFilter])

  const stats = useMemo(() => {
    if (!logsResponse?.data) return { total: 0, blocked: 0, allowed: 0 }
    
    const total = logsResponse.data.length
    const blocked = logsResponse.data.filter(log => log.blocked).length
    const allowed = total - blocked
    
    return { total, blocked, allowed }
  }, [logsResponse?.data])

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString()
  }

  const formatDevice = (device: any) => {
    if (!device) return 'Unknown'
    if (typeof device === 'string') return device
    return device.name || device.id || 'Unknown'
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">DNS Logs</h1>
            <p className="text-muted-foreground">Recent DNS queries and responses</p>
          </div>
          <Button variant="outline" disabled>
            <RefreshCw className="mr-2 h-4 w-4" />
            Loading...
          </Button>
        </div>

        <LoadingState message="Loading DNS logs..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">DNS Logs</h1>
            <p className="text-muted-foreground">Recent DNS queries and responses</p>
          </div>
          <Button variant="outline" onClick={() => refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry
          </Button>
        </div>

        <ErrorState 
          message="Failed to load DNS logs"
          onRetry={() => refetch()}
        />
      </div>
    )
  }

  return (
    <ApiErrorBoundary componentName="DNS Logs">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">DNS Logs</h1>
            <p className="text-muted-foreground">Recent DNS queries and responses</p>
          </div>
          <Button 
            variant="outline" 
            onClick={() => refetch()}
            disabled={isLoading}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {/* Quick Stats */}
        <div className="grid gap-6 md:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Queries</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-lego-blue">
                {formatNumber(stats.total)}
              </div>
              <p className="text-xs text-muted-foreground">
                Last 100 entries
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Blocked</CardTitle>
              <Shield className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-lego-red">
                {formatNumber(stats.blocked)}
              </div>
              <p className="text-xs text-muted-foreground">
                {stats.total > 0 ? Math.round((stats.blocked / stats.total) * 100) : 0}% blocked
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Allowed</CardTitle>
              <CheckCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-lego-green">
                {formatNumber(stats.allowed)}
              </div>
              <p className="text-xs text-muted-foreground">
                {stats.total > 0 ? Math.round((stats.allowed / stats.total) * 100) : 0}% allowed
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Filters</CardTitle>
            <CardDescription>Search and filter DNS logs</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col sm:flex-row gap-4">
              {/* Search Input */}
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search domains..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>

              {/* Status Filter Buttons */}
              <div className="flex gap-2">
                {[
                  { key: 'all', label: 'All', color: 'outline' },
                  { key: 'blocked', label: 'Blocked', color: 'destructive' },
                  { key: 'allowed', label: 'Allowed', color: 'default' }
                ].map(({ key, label, color }) => (
                  <Button
                    key={key}
                    variant={statusFilter === key ? (color as any) : 'outline'}
                    size="sm"
                    onClick={() => setStatusFilter(key as any)}
                    className={
                      statusFilter === key && key === 'allowed' 
                        ? 'bg-lego-green hover:bg-lego-green/90 text-white' 
                        : ''
                    }
                  >
                    {label}
                  </Button>
                ))}
              </div>
            </div>

            {/* Filter Summary */}
            {(searchQuery || statusFilter !== 'all') && (
              <div className="mt-4 text-sm text-muted-foreground">
                Showing {filteredLogs.length} of {stats.total} logs
                {searchQuery && ` matching "${searchQuery}"`}
                {statusFilter !== 'all' && ` (${statusFilter} only)`}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Logs Table */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              DNS Query Log
            </CardTitle>
            <CardDescription>
              {filteredLogs.length > 0 
                ? `${filteredLogs.length} recent DNS queries`
                : 'No logs match your filters'
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            {filteredLogs.length === 0 ? (
              <div className="text-center py-8">
                <Database className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
                <h3 className="text-lg font-semibold text-foreground mb-2">No logs found</h3>
                <p className="text-muted-foreground">
                  {searchQuery || statusFilter !== 'all'
                    ? 'Try adjusting your filters'
                    : 'No DNS logs available'
                  }
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-4 font-medium text-muted-foreground">Time</th>
                      <th className="text-left py-3 px-4 font-medium text-muted-foreground">Domain</th>
                      <th className="text-left py-3 px-4 font-medium text-muted-foreground">Device</th>
                      <th className="text-left py-3 px-4 font-medium text-muted-foreground">Status</th>
                      <th className="text-left py-3 px-4 font-medium text-muted-foreground">Type</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredLogs.map((log) => (
                      <tr key={log.id} className="border-b hover:bg-muted/50 transition-colors">
                        <td className="py-3 px-4 font-mono text-sm">
                          {formatTime(log.timestamp)}
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-medium">{log.domain}</div>
                        </td>
                        <td className="py-3 px-4 text-sm text-muted-foreground">
                          {formatDevice(log.device)}
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            {log.blocked ? (
                              <>
                                <XCircle className="h-4 w-4 text-lego-red" />
                                <span className="text-lego-red font-medium">Blocked</span>
                              </>
                            ) : (
                              <>
                                <CheckCircle className="h-4 w-4 text-lego-green" />
                                <span className="text-lego-green font-medium">Allowed</span>
                              </>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4 font-mono text-sm">
                          {log.query_type}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </ApiErrorBoundary>
  )
}
