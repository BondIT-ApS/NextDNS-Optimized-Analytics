import { useLogs, useLogsStats } from '@/hooks/useLogs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { SearchInput } from '@/components/SearchInput'
import { 
  RefreshCw, 
  Database,
  Shield,
  Clock,
  CheckCircle,
  XCircle
} from 'lucide-react'
import { formatNumber } from '@/lib/utils'
import { ApiErrorBoundary } from '@/components/ErrorBoundary'
import { LoadingState, ErrorState } from '@/components/LoadingSkeletons'
import { useState, useMemo, useEffect, useCallback } from 'react'

export function Logs() {
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'blocked' | 'allowed'>('all')
  
  // Debounce search query to prevent API calls on every keystroke
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchQuery(searchQuery)
    }, 500) // 500ms delay for more stability
    
    return () => clearTimeout(timer)
  }, [searchQuery])
  
  // Memoize the query parameters to prevent unnecessary re-renders
  const queryParams = useMemo(() => ({
    limit: 100,
    search: debouncedSearchQuery,
    status: statusFilter
  }), [debouncedSearchQuery, statusFilter])
  
  const { 
    data: logsResponse, 
    isLoading, 
    error, 
    refetch 
  } = useLogs(queryParams)
  
  // Get total stats from entire database
  const { 
    data: totalStats,
    isLoading: statsLoading
  } = useLogsStats()

  // Since filtering is now done on the backend, use the response data directly
  const filteredLogs = useMemo(() => {
    return logsResponse?.data || []
  }, [logsResponse?.data])

  const stats = useMemo(() => {
    // Current filtered results counts
    const filteredTotal = filteredLogs.length
    const filteredBlocked = filteredLogs.filter((log: any) => log.blocked).length
    const filteredAllowed = filteredTotal - filteredBlocked
    
    // Use total database stats for percentages
    const totalDatabaseStats = totalStats || { total: 0, blocked: 0, allowed: 0, blocked_percentage: 0, allowed_percentage: 0 }
    
    return {
      // Show filtered counts as main numbers
      total: filteredTotal,
      blocked: filteredBlocked,
      allowed: filteredAllowed,
      // Use database totals for percentage calculations
      totalInDatabase: totalDatabaseStats.total,
      blockedPercentage: totalDatabaseStats.blocked_percentage,
      allowedPercentage: totalDatabaseStats.allowed_percentage
    }
  }, [filteredLogs, totalStats])

  const formatTime = useCallback((timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString()
  }, [])

  const formatDevice = useCallback((device: any) => {
    if (!device) return 'Unknown'
    if (typeof device === 'string') return device
    return device.name || device.id || 'Unknown'
  }, [])
  
  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value)
  }, [])
  
  
  const handleStatusFilterChange = useCallback((status: 'all' | 'blocked' | 'allowed') => {
    setStatusFilter(status)
  }, [])

  if (isLoading || statsLoading) {
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
              <CardTitle className="text-sm font-medium">DNS Queries</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-lego-blue">
                {formatNumber(stats.total)}
              </div>
              <p className="text-xs text-muted-foreground">
                {debouncedSearchQuery || statusFilter !== 'all' 
                  ? `Filtered from ${formatNumber(stats.totalInDatabase)} total queries`
                  : `From ${formatNumber(stats.totalInDatabase)} total queries`
                }
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
                {stats.blockedPercentage}% of all queries
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
                {stats.allowedPercentage}% of all queries
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
              <SearchInput 
                value={searchQuery}
                onChange={handleSearchChange}
                placeholder="Search domains..."
              />

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
                    onClick={() => handleStatusFilterChange(key as any)}
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
            {(debouncedSearchQuery || statusFilter !== 'all') && (
              <div className="mt-4 text-sm text-muted-foreground">
                Showing {filteredLogs.length} of {stats.totalInDatabase} logs
                {debouncedSearchQuery && ` matching "${debouncedSearchQuery}"`}
                {statusFilter !== 'all' && ` (${statusFilter} only)`}
                {searchQuery !== debouncedSearchQuery && (
                  <span className="text-muted-foreground/70"> (searching...)</span>
                )}
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
                  {debouncedSearchQuery || statusFilter !== 'all'
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
                    {filteredLogs.map((log: any) => (
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
