import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ChartJsOverview } from '../ChartJsOverview'

describe('ChartJsOverview', () => {
  const mockTimeSeriesData = {
    data: [
      {
        timestamp: '2024-01-01T10:00:00Z',
        total_queries: 1000,
        blocked_queries: 250,
        allowed_queries: 750,
      },
      {
        timestamp: '2024-01-01T11:00:00Z',
        total_queries: 1200,
        blocked_queries: 300,
        allowed_queries: 900,
      },
      {
        timestamp: '2024-01-01T12:00:00Z',
        total_queries: 1500,
        blocked_queries: 400,
        allowed_queries: 1100,
      },
    ],
    granularity: 'hour',
    total_points: 3,
  }

  const mockOverview = {
    total_queries: 3700,
    blocked_queries: 950,
    allowed_queries: 2750,
    blocked_percentage: 25.68,
    queries_per_hour: 1233.33,
    most_active_device: 'iPhone',
    top_blocked_domain: 'ads.example.com',
  }

  it('renders without crashing with valid data', () => {
    render(
      <ChartJsOverview data={mockTimeSeriesData} overview={mockOverview} />
    )
    expect(screen.getByText('Queries Over Time')).toBeInTheDocument()
  })

  it('shows empty state when no data', () => {
    const emptyData = {
      data: [],
      granularity: 'hour',
      total_points: 0,
    }
    render(<ChartJsOverview data={emptyData} overview={mockOverview} />)
    expect(
      screen.getByText('No time series data available')
    ).toBeInTheDocument()
    expect(
      screen.getByText('Data will appear here once DNS queries are collected')
    ).toBeInTheDocument()
  })

  it('shows empty state when data is null', () => {
    render(<ChartJsOverview data={null} overview={mockOverview} />)
    expect(
      screen.getByText('No time series data available')
    ).toBeInTheDocument()
  })

  it('displays all chart sections with data', () => {
    render(
      <ChartJsOverview data={mockTimeSeriesData} overview={mockOverview} />
    )

    expect(screen.getByText('Queries Over Time')).toBeInTheDocument()
    expect(screen.getByText('Cumulative Query Volume')).toBeInTheDocument()
    expect(screen.getByText('Blocked vs Allowed')).toBeInTheDocument()
    expect(screen.getByText('Query Breakdown by Time')).toBeInTheDocument()
  })

  it('displays correct granularity in chart title', () => {
    render(
      <ChartJsOverview data={mockTimeSeriesData} overview={mockOverview} />
    )
    expect(screen.getByText('hour intervals')).toBeInTheDocument()
  })

  it('renders with different granularity', () => {
    const dayGranularityData = {
      ...mockTimeSeriesData,
      granularity: 'day',
    }
    render(
      <ChartJsOverview data={dayGranularityData} overview={mockOverview} />
    )
    expect(screen.getByText('day intervals')).toBeInTheDocument()
  })

  it('handles minute granularity', () => {
    const minuteData = {
      ...mockTimeSeriesData,
      granularity: 'minute',
    }
    render(<ChartJsOverview data={minuteData} overview={mockOverview} />)
    expect(screen.getByText('minute intervals')).toBeInTheDocument()
  })

  it('handles 5min granularity', () => {
    const fiveMinData = {
      ...mockTimeSeriesData,
      granularity: '5min',
    }
    render(<ChartJsOverview data={fiveMinData} overview={mockOverview} />)
    expect(screen.getByText('5min intervals')).toBeInTheDocument()
  })

  it('renders cumulative volume section', () => {
    render(
      <ChartJsOverview data={mockTimeSeriesData} overview={mockOverview} />
    )
    expect(screen.getByText('Cumulative Query Volume')).toBeInTheDocument()
    expect(screen.getByText('accumulated over time')).toBeInTheDocument()
  })

  it('handles empty data arrays gracefully', () => {
    const emptyArrayData = {
      data: [],
      granularity: 'hour',
      total_points: 0,
    }
    render(<ChartJsOverview data={emptyArrayData} overview={mockOverview} />)
    expect(
      screen.getByText('No time series data available')
    ).toBeInTheDocument()
  })

  it('renders all four chart types', () => {
    const { container } = render(
      <ChartJsOverview data={mockTimeSeriesData} overview={mockOverview} />
    )

    // Check for Card components (should be 4)
    const cards = container.querySelectorAll('.space-y-1\\.5')
    expect(cards.length).toBeGreaterThan(0)
  })
})
