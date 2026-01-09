import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ChartJsDomains } from '../ChartJsDomains'

describe('ChartJsDomains', () => {
  const mockData = {
    blocked_domains: [
      { domain: 'ads.example.com', count: 1000, percentage: 25.5 },
      { domain: 'tracker.example.com', count: 800, percentage: 20.4 },
      { domain: 'analytics.example.com', count: 600, percentage: 15.3 },
    ],
    allowed_domains: [
      { domain: 'google.com', count: 2000, percentage: 35.5 },
      { domain: 'github.com', count: 1500, percentage: 26.6 },
      { domain: 'stackoverflow.com', count: 1000, percentage: 17.7 },
    ],
  }

  it('renders without crashing with valid data', () => {
    render(<ChartJsDomains data={mockData} />)
    expect(screen.getByText('Top Blocked Domains')).toBeInTheDocument()
    expect(screen.getByText('Top Allowed Domains')).toBeInTheDocument()
  })

  it('renders statistics overview', () => {
    render(<ChartJsDomains data={mockData} />)
    expect(screen.getByText('Domain Statistics Overview')).toBeInTheDocument()
  })

  it('displays correct blocked and allowed domains count', () => {
    render(<ChartJsDomains data={mockData} />)
    // Check for "Blocked Domains" and "Allowed Domains" labels
    expect(screen.getByText('Blocked Domains')).toBeInTheDocument()
    expect(screen.getByText('Allowed Domains')).toBeInTheDocument()
  })

  it('displays total blocked requests count', () => {
    render(<ChartJsDomains data={mockData} />)
    // Total blocked: 1000 + 800 + 600 = 2400
    expect(screen.getByText('2,400')).toBeInTheDocument()
  })

  it('displays total allowed requests count', () => {
    render(<ChartJsDomains data={mockData} />)
    // Total allowed: 2000 + 1500 + 1000 = 4500
    expect(screen.getByText('4,500')).toBeInTheDocument()
  })

  it('shows empty state for blocked domains when no data', () => {
    const emptyData = {
      blocked_domains: [],
      allowed_domains: mockData.allowed_domains,
    }
    render(<ChartJsDomains data={emptyData} />)
    expect(
      screen.getByText('No blocked domains data available')
    ).toBeInTheDocument()
  })

  it('shows empty state for allowed domains when no data', () => {
    const emptyData = {
      blocked_domains: mockData.blocked_domains,
      allowed_domains: [],
    }
    render(<ChartJsDomains data={emptyData} />)
    expect(
      screen.getByText('No allowed domains data available')
    ).toBeInTheDocument()
  })

  it('handles null data gracefully', () => {
    render(<ChartJsDomains data={null} />)
    expect(screen.getByText('Top Blocked Domains')).toBeInTheDocument()
    expect(
      screen.getByText('No blocked domains data available')
    ).toBeInTheDocument()
    expect(
      screen.getByText('No allowed domains data available')
    ).toBeInTheDocument()
  })

  it('displays most blocked domains summary', () => {
    render(<ChartJsDomains data={mockData} />)
    expect(screen.getByText('Most Blocked:')).toBeInTheDocument()
    expect(screen.getByText('ads.example.com')).toBeInTheDocument()
    expect(screen.getByText('tracker.example.com')).toBeInTheDocument()
    expect(screen.getByText('analytics.example.com')).toBeInTheDocument()
  })

  it('displays most requested domains summary', () => {
    render(<ChartJsDomains data={mockData} />)
    expect(screen.getByText('Most Requested:')).toBeInTheDocument()
    expect(screen.getByText('google.com')).toBeInTheDocument()
    expect(screen.getByText('github.com')).toBeInTheDocument()
    expect(screen.getByText('stackoverflow.com')).toBeInTheDocument()
  })

  it('formats domain counts with locale strings', () => {
    render(<ChartJsDomains data={mockData} />)
    // Check that the counts are displayed with proper formatting (may appear multiple times)
    expect(screen.getAllByText('1,000').length).toBeGreaterThan(0)
  })

  it('only shows top 3 domains in summary', () => {
    const dataWithMany = {
      blocked_domains: [
        { domain: 'domain1.com', count: 100, percentage: 10 },
        { domain: 'domain2.com', count: 90, percentage: 9 },
        { domain: 'domain3.com', count: 80, percentage: 8 },
        { domain: 'domain4.com', count: 70, percentage: 7 },
        { domain: 'domain5.com', count: 60, percentage: 6 },
      ],
      allowed_domains: [],
    }
    render(<ChartJsDomains data={dataWithMany} />)

    // First 3 should be visible
    expect(screen.getByText('domain1.com')).toBeInTheDocument()
    expect(screen.getByText('domain2.com')).toBeInTheDocument()
    expect(screen.getByText('domain3.com')).toBeInTheDocument()

    // 4th and 5th should not be in the summary
    expect(screen.queryByText('domain4.com')).not.toBeInTheDocument()
    expect(screen.queryByText('domain5.com')).not.toBeInTheDocument()
  })
})
