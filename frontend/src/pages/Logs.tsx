import { useLogs, useLogsStats } from '@/hooks/useLogs'
import { Button } from '@/components/ui/button'
import { RefreshCw } from 'lucide-react'
import { ApiErrorBoundary } from '@/components/ErrorBoundary'
import { LoadingState, ErrorState } from '@/components/LoadingSkeletons'
import { StatsCards } from '@/components/StatsCards'
import { FilterPanel } from '@/components/FilterPanel'
import { LogsTable } from '@/components/LogsTable'
import { ProfileSelector } from '@/components/ProfileSelector'
import { DeviceFilter } from '@/components/DeviceFilter'
import { useState, useMemo, useEffect, useCallback, useTransition } from 'react'
import { useSearchParams } from 'react-router-dom'

export function Logs() {
  const [searchParams] = useSearchParams()

  // Initialize state from URL parameters
  const [searchQuery, setSearchQuery] = useState(
    () => searchParams.get('search') || ''
  )
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState(
    () => searchParams.get('search') || ''
  )
  const [statusFilter, setStatusFilter] = useState<
    'all' | 'blocked' | 'allowed'
  >(
    () => (searchParams.get('status') as 'all' | 'blocked' | 'allowed') || 'all'
  )
  const [selectedProfile, setSelectedProfile] = useState<string | undefined>(
    () => searchParams.get('profile') || undefined
  )
  const [selectedDevices, setSelectedDevices] = useState<string[]>(() => {
    const deviceParam = searchParams.get('device')
    return deviceParam ? [deviceParam] : []
  })
  const [, startTransition] = useTransition()

  // Debounce search query with transition for non-blocking updates
  useEffect(() => {
    const timer = setTimeout(() => {
      startTransition(() => {
        setDebouncedSearchQuery(searchQuery)
      })
    }, 500) // 500ms delay for more stability

    return () => clearTimeout(timer)
  }, [searchQuery])

  // Memoize the query parameters to prevent unnecessary re-renders
  const queryParams = useMemo(
    () => ({
      limit: 100,
      search: debouncedSearchQuery,
      status: statusFilter,
      profile: selectedProfile,
      devices: selectedDevices.length > 0 ? selectedDevices : undefined,
    }),
    [debouncedSearchQuery, statusFilter, selectedProfile, selectedDevices]
  )

  const { data: logsResponse, isLoading, error, refetch } = useLogs(queryParams)

  // Get total stats from entire database (or filtered by profile)
  const { data: totalStats, isLoading: statsLoading } =
    useLogsStats(selectedProfile)

  // Since filtering is now done on the backend, use the response data directly
  const filteredLogs = useMemo(() => {
    return logsResponse?.data || []
  }, [logsResponse?.data])

  const stats = useMemo(() => {
    // Current filtered results counts
    const filteredTotal = filteredLogs.length
    const filteredBlocked = filteredLogs.filter(
      (log: { blocked: boolean }) => log.blocked
    ).length
    const filteredAllowed = filteredTotal - filteredBlocked

    // Use total database stats for percentages
    const totalDatabaseStats = totalStats || {
      total: 0,
      blocked: 0,
      allowed: 0,
      blocked_percentage: 0,
      allowed_percentage: 0,
    }

    return {
      // Show filtered counts as main numbers
      total: filteredTotal,
      blocked: filteredBlocked,
      allowed: filteredAllowed,
      // Use database totals for percentage calculations
      totalInDatabase: totalDatabaseStats.total,
      blockedPercentage: totalDatabaseStats.blocked_percentage,
      allowedPercentage: totalDatabaseStats.allowed_percentage,
    }
  }, [filteredLogs, totalStats])

  const handleSearchChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setSearchQuery(e.target.value)
    },
    []
  )

  const handleStatusFilterChange = useCallback(
    (status: 'all' | 'blocked' | 'allowed') => {
      startTransition(() => {
        setStatusFilter(status)
      })
    },
    []
  )

  const handleProfileChange = useCallback((profileId: string | undefined) => {
    startTransition(() => {
      setSelectedProfile(profileId)
      // Reset device selection when profile changes
      setSelectedDevices([])
    })
  }, [])

  const handleDeviceSelectionChange = useCallback((devices: string[]) => {
    startTransition(() => {
      setSelectedDevices(devices)
    })
  }, [])

  if (isLoading || statsLoading) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">DNS Logs</h1>
            <p className="text-muted-foreground">
              Recent DNS queries and responses
            </p>
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
            <p className="text-muted-foreground">
              Recent DNS queries and responses
            </p>
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
            <p className="text-muted-foreground">
              Recent DNS queries and responses
            </p>
          </div>
          <Button
            variant="outline"
            onClick={() => refetch()}
            disabled={isLoading}
          >
            <RefreshCw
              className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`}
            />
            Refresh
          </Button>
        </div>

        {/* Quick Stats */}
        <StatsCards
          stats={stats}
          debouncedSearchQuery={debouncedSearchQuery}
          statusFilter={statusFilter}
        />

        {/* Profile Selector and Filters */}
        <div className="space-y-6">
          {/* Profile Selector */}
          <ProfileSelector
            selectedProfile={selectedProfile}
            onProfileChange={handleProfileChange}
            showStats={true}
          />

          {/* Device Filter and Search Filter - Side by Side */}
          <div className="flex flex-col lg:flex-row gap-6">
            <div className="flex-1">
              <DeviceFilter
                selectedProfile={selectedProfile}
                selectedDevices={selectedDevices}
                onDeviceSelectionChange={handleDeviceSelectionChange}
                timeRange="24h"
              />
            </div>

            <div className="flex-1">
              <FilterPanel
                searchQuery={searchQuery}
                onSearchChange={handleSearchChange}
                statusFilter={statusFilter}
                onStatusFilterChange={handleStatusFilterChange}
                debouncedSearchQuery={debouncedSearchQuery}
                filteredLogsCount={filteredLogs.length}
                totalLogsCount={stats.totalInDatabase}
                selectedProfile={selectedProfile}
              />
            </div>
          </div>
        </div>

        {/* Logs Table */}
        <LogsTable
          logs={filteredLogs}
          debouncedSearchQuery={debouncedSearchQuery}
          statusFilter={statusFilter}
        />
      </div>
    </ApiErrorBoundary>
  )
}
