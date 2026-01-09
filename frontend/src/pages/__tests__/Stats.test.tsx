import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Stats from '../Stats'
import * as apiModule from '../../lib/api'

// Mock the API module
vi.mock('../../lib/api', () => ({
  fetchWithAuth: vi.fn(),
}))

// Mock chart components that have complex dependencies
vi.mock('../../components/charts/ChartJsOverview', () => ({
  ChartJsOverview: () => <div data-testid="chart-overview">Overview Chart</div>,
}))

vi.mock('../../components/charts/ChartJsDomains', () => ({
  ChartJsDomains: () => <div data-testid="chart-domains">Domains Chart</div>,
}))

vi.mock('../../components/charts/ChartJsTlds', () => ({
  ChartJsTlds: () => <div data-testid="chart-tlds">TLDs Chart</div>,
}))

vi.mock('../../components/analytics/DeviceAnalytics', () => ({
  DeviceAnalytics: () => (
    <div data-testid="device-analytics">Device Analytics</div>
  ),
}))

// Mock data
const mockOverviewData = {
  total_queries: 12345,
  blocked_queries: 1234,
  allowed_queries: 11111,
  blocked_percentage: 10.0,
  queries_per_hour: 514,
  most_active_device: 'iPhone',
  top_blocked_domain: 'ads.example.com',
}

const mockTimeSeriesData = {
  data: [
    {
      timestamp: '2026-01-09T20:00:00Z',
      total_queries: 100,
      blocked_queries: 10,
      allowed_queries: 90,
    },
  ],
  granularity: 'hour',
  total_points: 1,
}

const mockDomainsData = {
  blocked_domains: [{ domain: 'ads.example.com', count: 50, percentage: 5.0 }],
  allowed_domains: [{ domain: 'google.com', count: 200, percentage: 20.0 }],
}

const mockTldsData = {
  blocked_tlds: [{ domain: 'example.com', count: 50, percentage: 5.0 }],
  allowed_tlds: [{ domain: 'google.com', count: 200, percentage: 20.0 }],
}

const mockProfilesData = {
  profiles: [
    {
      profile_id: 'abc123',
      record_count: 5000,
      last_activity: '2026-01-09T20:00:00Z',
    },
  ],
  total_profiles: 1,
}

const mockProfilesInfoData = {
  profiles: {
    abc123: {
      id: 'abc123',
      name: 'Home Network',
      fingerprint: 'abc123',
      created: '2025-01-01T00:00:00Z',
      updated: '2026-01-09T20:00:00Z',
    },
  },
  total_profiles: 1,
}

// Wrapper component with router
const StatsWithRouter = () => (
  <BrowserRouter>
    <Stats />
  </BrowserRouter>
)

describe('🧱 Stats Page', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear()

    // Reset all mocks
    vi.clearAllMocks()

    // Setup default mock implementation
    vi.mocked(apiModule.fetchWithAuth).mockImplementation((url: string): Promise<Response> => {
      if (url.includes('/stats/overview')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockOverviewData),
        } as Response)
      }
      if (url.includes('/stats/timeseries')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockTimeSeriesData),
        } as Response)
      }
      if (url.includes('/stats/domains')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockDomainsData),
        } as Response)
      }
      if (url.includes('/stats/tlds')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockTldsData),
        } as Response)
      }
      if (url.includes('/profiles/info')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockProfilesInfoData),
        } as Response)
      }
      if (url.includes('/profiles')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockProfilesData),
        } as Response)
      }
      return Promise.resolve({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        text: () => Promise.resolve('Not Found'),
      } as Response)
    })
  })

  describe('Rendering', () => {
    it('should render page header', async () => {
      render(<StatsWithRouter />)

      await waitFor(() => {
        expect(screen.getByText('Analytics Dashboard')).toBeInTheDocument()
      })

      expect(
        screen.getByText(/Comprehensive DNS analytics/)
      ).toBeInTheDocument()
    })

    it('should render loading state initially', () => {
      render(<StatsWithRouter />)

      // Should show loading spinner
      const spinner = document.querySelector('.animate-spin')
      expect(spinner).toBeInTheDocument()
    })

    it('should render time range selector', async () => {
      render(<StatsWithRouter />)

      await waitFor(() => {
        expect(screen.getByText('Time Range')).toBeInTheDocument()
      })

      expect(screen.getByText('1 Hour')).toBeInTheDocument()
      expect(screen.getByText('24 Hours')).toBeInTheDocument()
      expect(screen.getByText('7 Days')).toBeInTheDocument()
      expect(screen.getByText('30 Days')).toBeInTheDocument()
      expect(screen.getByText('All Data')).toBeInTheDocument()
    })

    it('should render profile selector', async () => {
      render(<StatsWithRouter />)

      await waitFor(() => {
        expect(screen.getByText('Profile Filter')).toBeInTheDocument()
      })

      expect(screen.getByText('All Profiles')).toBeInTheDocument()
    })
  })

  describe('Stats Cards', () => {
    it('should display total queries card', async () => {
      render(<StatsWithRouter />)

      await waitFor(() => {
        expect(screen.getByText('Total Queries')).toBeInTheDocument()
      })

      expect(screen.getByText('12.3K')).toBeInTheDocument()
      expect(screen.getByText('514/hour avg')).toBeInTheDocument()
    })

    it('should display blocked queries card', async () => {
      render(<StatsWithRouter />)

      await waitFor(() => {
        expect(screen.getByText('Blocked')).toBeInTheDocument()
      })

      expect(screen.getByText('10.0%')).toBeInTheDocument()
      expect(screen.getByText('1.2K queries')).toBeInTheDocument()
    })

    it('should display most active device', async () => {
      render(<StatsWithRouter />)

      await waitFor(() => {
        expect(screen.getByText('Most Active Device')).toBeInTheDocument()
      })

      expect(screen.getByText('iPhone')).toBeInTheDocument()
    })

    it('should display top blocked domain', async () => {
      render(<StatsWithRouter />)

      await waitFor(() => {
        expect(screen.getByText('Top Blocked')).toBeInTheDocument()
      })

      expect(screen.getByText('ads.example.com')).toBeInTheDocument()
    })

    it('should handle null values in stats', async () => {
      vi.mocked(apiModule.fetchWithAuth).mockImplementation((url: string): Promise<Response> => {
        if (url.includes('/stats/overview')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              ...mockOverviewData,
              most_active_device: null,
              top_blocked_domain: null,
            }),
          } as Response)
        }
        if (url.includes('/stats/timeseries')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockTimeSeriesData),
          } as Response)
        }
        if (url.includes('/stats/domains')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockDomainsData),
          } as Response)
        }
        if (url.includes('/stats/tlds')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockTldsData),
          } as Response)
        }
        if (url.includes('/profiles/info')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockProfilesInfoData),
          } as Response)
        }
        if (url.includes('/profiles')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockProfilesData),
          } as Response)
        }
        return Promise.resolve({
          ok: false,
          status: 404,
          statusText: 'Not Found',
          text: () => Promise.resolve('Not Found'),
        } as Response)
      })

      render(<StatsWithRouter />)

      await waitFor(() => {
        expect(screen.getByText('Unknown')).toBeInTheDocument()
      })

      expect(screen.getByText('None')).toBeInTheDocument()
    })
  })

  describe('Tab Navigation', () => {
    it('should render all tab options', async () => {
      render(<StatsWithRouter />)

      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument()
      })

      expect(screen.getByText('Domains')).toBeInTheDocument()
      expect(screen.getByText('Devices')).toBeInTheDocument()
      expect(screen.getByText('Parent Domains')).toBeInTheDocument()
    })

    it('should show overview chart by default', async () => {
      render(<StatsWithRouter />)

      await waitFor(() => {
        expect(screen.getByTestId('chart-overview')).toBeInTheDocument()
      })
    })
  })

  describe('Error Handling', () => {
    it('should display error message when API fails', async () => {
      vi.mocked(apiModule.fetchWithAuth).mockImplementation((): Promise<Response> =>
        Promise.resolve({
          ok: false,
          status: 500,
          statusText: 'Internal Server Error',
          text: () => Promise.resolve('Server error'),
        } as Response)
      )

      render(<StatsWithRouter />)

      await waitFor(() => {
        expect(screen.getByText(/Error loading stats/)).toBeInTheDocument()
      })
    })
  })

  describe('Number Formatting', () => {
    it('should format large numbers correctly', async () => {
      vi.mocked(apiModule.fetchWithAuth).mockImplementation((url: string): Promise<Response> => {
        if (url.includes('/stats/overview')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              ...mockOverviewData,
              total_queries: 1500000, // Should show as 1.5M
              queries_per_hour: 2500, // Should show as 2.5K
            }),
          } as Response)
        }
        if (url.includes('/stats/timeseries')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockTimeSeriesData),
          } as Response)
        }
        if (url.includes('/stats/domains')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockDomainsData),
          } as Response)
        }
        if (url.includes('/stats/tlds')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockTldsData),
          } as Response)
        }
        if (url.includes('/profiles/info')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockProfilesInfoData),
          } as Response)
        }
        if (url.includes('/profiles')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockProfilesData),
          } as Response)
        }
        return Promise.resolve({
          ok: false,
          status: 404,
          statusText: 'Not Found',
          text: () => Promise.resolve('Not Found'),
        } as Response)
      })

      render(<StatsWithRouter />)

      await waitFor(() => {
        expect(screen.getByText('1.5M')).toBeInTheDocument()
      })

      expect(screen.getByText('2.5K/hour avg')).toBeInTheDocument()
    })
  })

  describe('Profile Selection', () => {
    it('should render profile with name from info', async () => {
      render(<StatsWithRouter />)

      await waitFor(() => {
        expect(screen.getByText(/Home Network/)).toBeInTheDocument()
      })
    })

    it('should show profile count', async () => {
      render(<StatsWithRouter />)

      await waitFor(() => {
        expect(screen.getByText(/5000/)).toBeInTheDocument()
      })
    })
  })
})
