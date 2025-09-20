import { useLogs, useLogsStats } from '@/hooks/useLogs'
import { Button } from '@/components/ui/button'
import { RefreshCw } from 'lucide-react'
import { ApiErrorBoundary } from '@/components/ErrorBoundary'
import { LoadingState, ErrorState } from '@/components/LoadingSkeletons'
import { StatsCards } from '@/components/StatsCards'
import { FilterPanel } from '@/components/FilterPanel'
import { LogsTable } from '@/components/LogsTable'
import { ProfileSelector } from '@/components/ProfileSelector'
import { useState, useMemo, useEffect, useCallback, useTransition } from 'react'

export function Logs() {
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<
    'all' | 'blocked' | 'allowed'
  >('all')
  const [selectedProfile, setSelectedProfile] = useState<string | undefined>(
    undefined
  )
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
    }),
    [debouncedSearchQuery, statusFilter, selectedProfile]
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
      (log: any) => log.blocked
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

        {/* Profile Selector and Search Filter - Side by Side */}
        <div className="flex flex-col lg:flex-row gap-6">
          <div className="flex-1">
            <ProfileSelector
              selectedProfile={selectedProfile}
              onProfileChange={handleProfileChange}
              showStats={true}
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
