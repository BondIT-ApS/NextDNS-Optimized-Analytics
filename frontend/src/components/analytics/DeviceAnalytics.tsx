import { useState, useEffect, useMemo, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  Smartphone,
  Laptop,
  Monitor,
  Router,
  Search,
  X,
  Shield,
  CheckCircle,
  Clock,
  Filter,
  SortAsc,
  SortDesc,
  Activity,
  ExternalLink,
} from 'lucide-react'
import { apiClient } from '@/services/api'
import type { DeviceUsageItem, DeviceFilters } from '@/types/api'
import { formatNumber } from '@/lib/utils'
import { LoadingState, ErrorState } from '@/components/LoadingSkeletons'

interface DeviceAnalyticsProps {
  selectedProfile?: string
  timeRange?: string
  excludedDomains?: string[]
  className?: string
}

type SortField =
  | 'device_name'
  | 'total_queries'
  | 'blocked_percentage'
  | 'last_activity'
type SortOrder = 'asc' | 'desc'

export function DeviceAnalytics({
  selectedProfile,
  timeRange = '24h',
  excludedDomains = [],
  className = '',
}: DeviceAnalyticsProps) {
  const navigate = useNavigate()
  const [devices, setDevices] = useState<DeviceUsageItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filter states
  const [searchQuery, setSearchQuery] = useState('')
  const [excludedDevices, setExcludedDevices] = useState<string[]>([
    'Unidentified Device',
  ])
  const [limitDevices, setLimitDevices] = useState(20)
  const [sortField, setSortField] = useState<SortField>('total_queries')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')

  // Fetch device data
  const fetchDeviceData = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const filters: DeviceFilters = {
        profile: selectedProfile || undefined,
        time_range: timeRange,
        limit: 50, // Get more data for client-side filtering
        exclude: excludedDevices.length > 0 ? excludedDevices : undefined,
      }

      const response = await apiClient.getDeviceStats(
        filters.profile,
        filters.time_range,
        filters.limit,
        filters.exclude,
        excludedDomains
      )

      setDevices(response.devices)
    } catch (err) {
      console.error('Error fetching device data:', err)
      setError(
        err instanceof Error ? err.message : 'Failed to fetch device data'
      )
    } finally {
      setLoading(false)
    }
  }, [selectedProfile, timeRange, excludedDevices, excludedDomains])

  useEffect(() => {
    fetchDeviceData()
  }, [selectedProfile, timeRange, excludedDevices, excludedDomains, fetchDeviceData])

  // Filter and sort devices
  const filteredAndSortedDevices = useMemo(() => {
    let filtered = devices

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(device =>
        device.device_name.toLowerCase().includes(query)
      )
    }

    // Apply sorting
    filtered = [...filtered].sort((a, b) => {
      let aValue: string | number = a[sortField]
      let bValue: string | number = b[sortField]

      // Handle string comparison for device names
      if (sortField === 'device_name') {
        aValue = (aValue as string).toLowerCase()
        bValue = (bValue as string).toLowerCase()
      }

      // Handle date comparison for last_activity
      if (sortField === 'last_activity') {
        aValue = new Date(aValue).getTime()
        bValue = new Date(bValue).getTime()
      }

      if (sortOrder === 'asc') {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0
      }
    })

    // Apply limit
    return filtered.slice(0, limitDevices)
  }, [devices, searchQuery, sortField, sortOrder, limitDevices])

  // Device icon based on device name
  const getDeviceIcon = (deviceName: string) => {
    const name = deviceName.toLowerCase()
    if (
      name.includes('iphone') ||
      name.includes('android') ||
      name.includes('mobile') ||
      name.includes('tablet') ||
      name.includes('ipad')
    ) {
      return <Smartphone className="h-5 w-5 text-lego-blue" />
    }
    if (
      name.includes('macbook') ||
      name.includes('laptop') ||
      name.includes('pc')
    ) {
      return <Laptop className="h-5 w-5 text-lego-green" />
    }
    if (name.includes('router') || name.includes('gateway')) {
      return <Router className="h-5 w-5 text-lego-purple" />
    }
    return <Monitor className="h-5 w-5 text-lego-yellow" />
  }

  // Format last activity time
  const formatLastActivity = (timestamp: string) => {
    const now = new Date()
    const activity = new Date(timestamp)
    const diffMs = now.getTime() - activity.getTime()
    const diffMins = Math.floor(diffMs / (1000 * 60))
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    return `${diffDays}d ago`
  }

  // Handle device exclusion
  const toggleDeviceExclusion = (deviceName: string) => {
    setExcludedDevices(prev => {
      if (prev.includes(deviceName)) {
        return prev.filter(name => name !== deviceName)
      } else {
        return [...prev, deviceName]
      }
    })
  }

  // Clear exclusions
  const clearExclusions = () => {
    setExcludedDevices([])
  }

  // Navigate to logs page with device filter
  const handleViewLogs = (deviceName: string) => {
    const params = new URLSearchParams()

    // Apply current filters from the stats page
    if (selectedProfile) {
      params.append('profile', selectedProfile)
    }
    if (timeRange) {
      params.append('timeRange', timeRange)
    }

    // Add device filter
    params.append('device', deviceName)

    // Navigate to logs page with query parameters
    navigate(`/logs?${params.toString()}`)
  }

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Device Analytics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <LoadingState message="Loading device analytics..." />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Device Analytics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ErrorState
            message={error}
            onRetry={fetchDeviceData}
            className="py-8"
          />
        </CardContent>
      </Card>
    )
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-lego-blue" />
            Device Usage Analytics
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            DNS query activity by device with comprehensive usage statistics
          </p>
        </CardHeader>

        {/* Filters */}
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search devices..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Sort Field */}
            <label htmlFor="sort-field" className="sr-only">
              Sort field
            </label>
            <select
              id="sort-field"
              value={sortField}
              onChange={e => setSortField(e.target.value as SortField)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="device_name">Sort by: Device Name</option>
              <option value="total_queries">Sort by: Total Queries</option>
              <option value="blocked_percentage">Sort by: Blocked %</option>
              <option value="last_activity">Sort by: Last Activity</option>
            </select>

            {/* Sort Order */}
            <Button
              variant="outline"
              onClick={() =>
                setSortOrder(prev => (prev === 'asc' ? 'desc' : 'asc'))
              }
              className="flex items-center gap-2"
            >
              {sortOrder === 'asc' ? (
                <SortAsc className="h-4 w-4" />
              ) : (
                <SortDesc className="h-4 w-4" />
              )}
              {sortOrder === 'asc' ? 'Ascending' : 'Descending'}
            </Button>

            {/* Limit */}
            <label className="sr-only" htmlFor="limit-select">
              Limit
            </label>
            <select
              id="limit-select"
              value={limitDevices.toString()}
              onChange={e => setLimitDevices(parseInt(e.target.value))}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="10">Top 10</option>
              <option value="20">Top 20</option>
              <option value="50">Top 50</option>
            </select>
          </div>

          {/* Exclusions */}
          {excludedDevices.length > 0 && (
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm text-muted-foreground flex items-center gap-1">
                <Filter className="h-3 w-3" />
                Excluded devices:
              </span>
              {excludedDevices.map(device => (
                <Badge
                  key={device}
                  variant="secondary"
                  className="flex items-center gap-1"
                >
                  {device}
                  <X
                    className="h-3 w-3 cursor-pointer"
                    onClick={() => toggleDeviceExclusion(device)}
                  />
                </Badge>
              ))}
              <Button
                variant="ghost"
                size="sm"
                onClick={clearExclusions}
                className="text-lego-red hover:text-lego-red/80"
              >
                Clear all
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Device Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filteredAndSortedDevices.map((device, index) => (
          <Card
            key={device.device_name}
            className="hover:shadow-md transition-shadow"
          >
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  {getDeviceIcon(device.device_name)}
                  <div className="min-w-0 flex-1">
                    <CardTitle className="text-base truncate">
                      {device.device_name}
                    </CardTitle>
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      {formatLastActivity(device.last_activity)}
                    </div>
                  </div>
                </div>
                <Badge variant="outline" className="ml-2">
                  #{index + 1}
                </Badge>
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              {/* Total Queries */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-muted-foreground">
                    Total Queries
                  </span>
                  <span className="font-semibold text-lego-blue">
                    {formatNumber(device.total_queries)}
                  </span>
                </div>
              </div>

              {/* Blocked vs Allowed */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1">
                    <Shield className="h-3 w-3 text-lego-red" />
                    <span className="text-sm text-muted-foreground">
                      Blocked
                    </span>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold text-lego-red">
                      {device.blocked_percentage.toFixed(1)}%
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {formatNumber(device.blocked_queries)}
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1">
                    <CheckCircle className="h-3 w-3 text-lego-green" />
                    <span className="text-sm text-muted-foreground">
                      Allowed
                    </span>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold text-lego-green">
                      {device.allowed_percentage.toFixed(1)}%
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {formatNumber(device.allowed_queries)}
                    </div>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-secondary rounded-full h-2">
                  <div
                    className="bg-lego-red h-2 rounded-l-full transition-all duration-300"
                    style={{ width: `${device.blocked_percentage}%` }}
                  />
                </div>
              </div>

              {/* Actions */}
              <div className="pt-2 border-t border-border">
                <div className="grid grid-cols-2 gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleDeviceExclusion(device.device_name)}
                    className={`${
                      excludedDevices.includes(device.device_name)
                        ? 'text-lego-green hover:text-lego-green/80'
                        : 'text-lego-orange hover:text-lego-orange/80'
                    }`}
                  >
                    {excludedDevices.includes(device.device_name)
                      ? 'Include'
                      : 'Exclude'}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleViewLogs(device.device_name)}
                    className="text-lego-blue hover:text-lego-blue/80 flex items-center gap-1"
                  >
                    <ExternalLink className="h-3 w-3" />
                    View Logs
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Empty State */}
      {filteredAndSortedDevices.length === 0 && !loading && (
        <Card>
          <CardContent className="py-12 text-center">
            <Activity className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No devices found</h3>
            <p className="text-muted-foreground mb-4">
              {searchQuery
                ? `No devices match "${searchQuery}". Try adjusting your search or filters.`
                : 'No devices have been active in the selected time range.'}
            </p>
            {(searchQuery || excludedDevices.length > 0) && (
              <Button
                variant="outline"
                onClick={() => {
                  setSearchQuery('')
                  clearExclusions()
                }}
              >
                Clear Filters
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Results Summary */}
      {filteredAndSortedDevices.length > 0 && (
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>
                Showing {filteredAndSortedDevices.length} of {devices.length}{' '}
                devices
                {searchQuery && ` matching "${searchQuery}"`}
              </span>
              <span>
                Time range: {timeRange} • Profile:{' '}
                {selectedProfile || 'All profiles'}
              </span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
