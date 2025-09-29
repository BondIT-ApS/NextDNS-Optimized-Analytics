import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs'
import { Button } from '../components/ui/button'
import {
  BarChart3,
  TrendingUp,
  Shield,
  Zap,
  Monitor,
  Globe,
  Smartphone,
} from 'lucide-react'

// Chart components
import { ChartJsOverview } from '../components/charts/ChartJsOverview'
import { ChartJsDomains } from '../components/charts/ChartJsDomains'
import { ChartJsTlds } from '../components/charts/ChartJsTlds'
import { DeviceAnalytics } from '../components/analytics/DeviceAnalytics'

// Profile data interface
interface Profile {
  profile_id: string
  record_count: number
  last_activity: string
}

interface ProfileInfo {
  id: string
  name: string
  fingerprint?: string
  created?: string
  updated?: string
  error?: string
}

interface ProfilesResponse {
  profiles: Profile[]
  total_profiles: number
}

interface ProfilesInfoResponse {
  profiles: Record<string, ProfileInfo>
  total_profiles: number
}

// Types for API responses
interface StatsOverview {
  total_queries: number
  blocked_queries: number
  allowed_queries: number
  blocked_percentage: number
  queries_per_hour: number
  most_active_device: string | null
  top_blocked_domain: string | null
}

interface TimeSeriesDataPoint {
  timestamp: string
  total_queries: number
  blocked_queries: number
  allowed_queries: number
}

interface TimeSeriesData {
  data: TimeSeriesDataPoint[]
  granularity: string
  total_points: number
}

interface TopDomainsData {
  blocked_domains: { domain: string; count: number; percentage: number }[]
  allowed_domains: { domain: string; count: number; percentage: number }[]
}

interface TopTLDsData {
  blocked_tlds: { domain: string; count: number; percentage: number }[]
  allowed_tlds: { domain: string; count: number; percentage: number }[]
}

const TIME_RANGES = [
  { value: '1h', label: '1 Hour' },
  { value: '24h', label: '24 Hours' },
  { value: '7d', label: '7 Days' },
  { value: '30d', label: '30 Days' },
  { value: 'all', label: 'All Data' },
]

export default function Stats() {
  const [searchParams, setSearchParams] = useSearchParams()

  // State management
  const [selectedProfile, setSelectedProfile] = useState<string>('all')
  const [timeRange, setTimeRange] = useState<string>('24h')
  const [activeTab, setActiveTab] = useState<string>('overview')

  // Data state
  const [overview, setOverview] = useState<StatsOverview | null>(null)
  const [timeSeries, setTimeSeries] = useState<TimeSeriesData | null>(null)
  const [topDomains, setTopDomains] = useState<TopDomainsData | null>(null)
  const [topTlds, setTopTlds] = useState<TopTLDsData | null>(null)
  const [profiles, setProfiles] = useState<ProfilesResponse | null>(null)
  const [profilesInfo, setProfilesInfo] = useState<ProfilesInfoResponse | null>(
    null
  )
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Load persisted preferences
  useEffect(() => {
    const savedProfile = localStorage.getItem('stats_selected_profile')
    const savedTimeRange = localStorage.getItem('stats_time_range')
    const savedTab = localStorage.getItem('stats_active_tab')

    if (savedProfile) setSelectedProfile(savedProfile)
    if (savedTimeRange) setTimeRange(savedTimeRange)
    if (savedTab) setActiveTab(savedTab)

    // Also check URL params
    const profileParam = searchParams.get('profile')
    const timeParam = searchParams.get('time')
    const tabParam = searchParams.get('tab')

    if (profileParam) setSelectedProfile(profileParam)
    if (timeParam) setTimeRange(timeParam)
    if (tabParam) setActiveTab(tabParam)
  }, [searchParams])

  // Persist preferences
  useEffect(() => {
    localStorage.setItem('stats_selected_profile', selectedProfile)
    localStorage.setItem('stats_time_range', timeRange)
    localStorage.setItem('stats_active_tab', activeTab)

    // Update URL params
    const params = new URLSearchParams()
    if (selectedProfile !== 'all') params.set('profile', selectedProfile)
    if (timeRange !== '24h') params.set('time', timeRange)
    if (activeTab !== 'overview') params.set('tab', activeTab)

    setSearchParams(params, { replace: true })
  }, [selectedProfile, timeRange, activeTab, setSearchParams])

  // Fetch data
  const fetchData = async () => {
    setLoading(true)
    setError(null)

    try {
      const baseUrl = '/api'
      const params = new URLSearchParams()
      if (selectedProfile !== 'all') params.set('profile', selectedProfile)
      params.set('time_range', timeRange)

      console.log('Fetching stats data with params:', params.toString())

      // Fetch overview data
      console.log(
        'Fetching overview data from:',
        `${baseUrl}/stats/overview?${params}`
      )
      const overviewResponse = await fetch(
        `${baseUrl}/stats/overview?${params}`
      )
      if (!overviewResponse.ok) {
        const errorText = await overviewResponse.text()
        console.error('Overview API error:', overviewResponse.status, errorText)
        throw new Error(
          `Failed to fetch overview data: ${overviewResponse.status} ${overviewResponse.statusText}`
        )
      }
      const overviewData = await overviewResponse.json()
      console.log('Overview data received:', overviewData)
      setOverview(overviewData)

      // Fetch time series data
      console.log(
        'Fetching timeseries data from:',
        `${baseUrl}/stats/timeseries?${params}`
      )
      const timeSeriesResponse = await fetch(
        `${baseUrl}/stats/timeseries?${params}`
      )
      if (!timeSeriesResponse.ok) {
        const errorText = await timeSeriesResponse.text()
        console.error(
          'Timeseries API error:',
          timeSeriesResponse.status,
          errorText
        )
        throw new Error(
          `Failed to fetch time series data: ${timeSeriesResponse.status} ${timeSeriesResponse.statusText}`
        )
      }
      const timeSeriesData = await timeSeriesResponse.json()
      console.log('Timeseries data received:', timeSeriesData)
      setTimeSeries(timeSeriesData)

      // Fetch top domains data
      console.log(
        'Fetching domains data from:',
        `${baseUrl}/stats/domains?${params}`
      )
      const domainsResponse = await fetch(`${baseUrl}/stats/domains?${params}`)
      if (!domainsResponse.ok) {
        const errorText = await domainsResponse.text()
        console.error('Domains API error:', domainsResponse.status, errorText)
        throw new Error(
          `Failed to fetch domains data: ${domainsResponse.status} ${domainsResponse.statusText}`
        )
      }
      const domainsData = await domainsResponse.json()
      console.log('Domains data received:', domainsData)
      setTopDomains(domainsData)

      // Fetch TLD data
      console.log(
        'Fetching TLDs data from:',
        `${baseUrl}/stats/tlds?${params}`
      )
      const tldsResponse = await fetch(`${baseUrl}/stats/tlds?${params}`)
      if (!tldsResponse.ok) {
        const errorText = await tldsResponse.text()
        console.error('TLDs API error:', tldsResponse.status, errorText)
        throw new Error(
          `Failed to fetch TLDs data: ${tldsResponse.status} ${tldsResponse.statusText}`
        )
      }
      const tldsData = await tldsResponse.json()
      console.log('TLDs data received:', tldsData)
      setTopTlds(tldsData)
    } catch (err) {
      console.error('Error fetching stats:', err)
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  // Fetch profiles on component mount
  useEffect(() => {
    const fetchProfiles = async () => {
      try {
        const response = await fetch('/api/profiles')
        if (response.ok) {
          const profilesData = await response.json()
          console.log('Profiles data received:', profilesData)
          setProfiles(profilesData)
        }

        // Also fetch profile info to get real names
        const infoResponse = await fetch('/api/profiles/info')
        if (infoResponse.ok) {
          const profilesInfoData = await infoResponse.json()
          console.log('Profiles info received:', profilesInfoData)
          setProfilesInfo(profilesInfoData)
        }
      } catch (err) {
        console.error('Error fetching profiles:', err)
      }
    }
    fetchProfiles()
  }, [])

  // Fetch data when dependencies change
  useEffect(() => {
    fetchData()
  }, [selectedProfile, timeRange])

  // Format numbers for display
  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
    return num.toString()
  }

  const formatPercentage = (num: number) => `${num.toFixed(1)}%`

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <BarChart3 className="h-8 w-8 text-blue-600" />
            Analytics Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Comprehensive DNS analytics and insights for your NextDNS profiles
          </p>
        </div>
      </div>

      {/* Controls */}
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Profile Selector */}
        <Card className="flex-1">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">
              Profile Filter
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              <Button
                variant={selectedProfile === 'all' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedProfile('all')}
              >
                All Profiles
              </Button>
              {profiles?.profiles.map(profile => {
                const profileInfo = profilesInfo?.profiles[profile.profile_id]
                const displayName = profileInfo?.name
                  ? `${profileInfo.name} (${profile.profile_id})`
                  : `Profile ${profile.profile_id}`

                return (
                  <Button
                    key={profile.profile_id}
                    variant={
                      selectedProfile === profile.profile_id
                        ? 'default'
                        : 'outline'
                    }
                    size="sm"
                    onClick={() => setSelectedProfile(profile.profile_id)}
                    className="flex items-center gap-1"
                  >
                    <span>{displayName}</span>
                    <span className="text-xs opacity-60">
                      ({profile.record_count})
                    </span>
                  </Button>
                )
              })}
            </div>
          </CardContent>
        </Card>

        {/* Time Range Selector */}
        <Card className="flex-1">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Time Range</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {TIME_RANGES.map(range => (
                <Button
                  key={range.value}
                  variant={timeRange === range.value ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setTimeRange(range.value)}
                >
                  {range.label}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <Card className="border-red-200 bg-red-50 dark:bg-red-900/20">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
              <Shield className="h-5 w-5" />
              <span className="font-medium">Error loading stats: {error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content */}
      {!loading && !error && overview && (
        <>
          {/* Key Metrics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Total Queries
                </CardTitle>
                <Globe className="h-4 w-4 text-blue-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatNumber(overview.total_queries)}
                </div>
                <p className="text-xs text-muted-foreground">
                  {formatNumber(overview.queries_per_hour)}/hour avg
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Blocked</CardTitle>
                <Shield className="h-4 w-4 text-red-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">
                  {formatPercentage(overview.blocked_percentage)}
                </div>
                <p className="text-xs text-muted-foreground">
                  {formatNumber(overview.blocked_queries)} queries
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Most Active Device
                </CardTitle>
                <Monitor className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-lg font-bold truncate">
                  {overview.most_active_device || 'Unknown'}
                </div>
                <p className="text-xs text-muted-foreground">Top device</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Top Blocked
                </CardTitle>
                <Zap className="h-4 w-4 text-orange-600" />
              </CardHeader>
              <CardContent>
                <div className="text-sm font-bold truncate">
                  {overview.top_blocked_domain || 'None'}
                </div>
                <p className="text-xs text-muted-foreground">
                  Most blocked domain
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Tabbed Charts */}
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="overview" className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Overview
              </TabsTrigger>
              <TabsTrigger value="domains" className="flex items-center gap-2">
                <Globe className="h-4 w-4" />
                Domains
              </TabsTrigger>
              <TabsTrigger value="devices" className="flex items-center gap-2">
                <Smartphone className="h-4 w-4" />
                Devices
              </TabsTrigger>
              <TabsTrigger value="tlds" className="flex items-center gap-2">
                <Globe className="h-4 w-4" />
                Parent Domains
              </TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="mt-6">
              <ChartJsOverview data={timeSeries} overview={overview} />
            </TabsContent>

            <TabsContent value="domains" className="mt-6">
              <ChartJsDomains data={topDomains} />
            </TabsContent>

            <TabsContent value="devices" className="mt-6">
              <DeviceAnalytics
                selectedProfile={
                  selectedProfile === 'all' ? undefined : selectedProfile
                }
                timeRange={timeRange}
              />
            </TabsContent>

            <TabsContent value="tlds" className="mt-6">
              <ChartJsTlds data={topTlds} />
            </TabsContent>
          </Tabs>
        </>
      )}
    </div>
  )
}
