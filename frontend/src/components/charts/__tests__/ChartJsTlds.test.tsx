import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ChartJsTlds } from '../ChartJsTlds'

describe('ChartJsTlds', () => {
  const mockData = {
    blocked_tlds: [
      { domain: '.cn', count: 1500, percentage: 30.5 },
      { domain: '.xyz', count: 1200, percentage: 24.4 },
      { domain: '.ru', count: 800, percentage: 16.3 },
    ],
    allowed_tlds: [
      { domain: '.com', count: 5000, percentage: 45.5 },
      { domain: '.net', count: 2500, percentage: 22.7 },
      { domain: '.org', count: 1500, percentage: 13.6 },
    ],
  }

  it('renders without crashing with valid data', () => {
    render(<ChartJsTlds data={mockData} />)
    expect(screen.getByText('Top Blocked Parent Domains')).toBeInTheDocument()
    expect(screen.getByText('Top Allowed Parent Domains')).toBeInTheDocument()
  })

  it('renders statistics overview', () => {
    render(<ChartJsTlds data={mockData} />)
    expect(screen.getByText('Parent Domain Statistics')).toBeInTheDocument()
  })

  it('displays correct blocked and allowed TLDs labels', () => {
    render(<ChartJsTlds data={mockData} />)
    // Check for "Blocked Parent Domains" and "Allowed Parent Domains" labels
    expect(screen.getAllByText('Blocked Parent Domains').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Allowed Parent Domains').length).toBeGreaterThan(0)
  })

  it('displays total blocked requests count', () => {
    render(<ChartJsTlds data={mockData} />)
    // Total blocked: 1500 + 1200 + 800 = 3500
    expect(screen.getByText('3,500')).toBeInTheDocument()
  })

  it('displays total allowed requests count', () => {
    render(<ChartJsTlds data={mockData} />)
    // Total allowed: 5000 + 2500 + 1500 = 9000
    expect(screen.getByText('9,000')).toBeInTheDocument()
  })

  it('shows empty state for blocked TLDs when no data', () => {
    const emptyData = {
      blocked_tlds: [],
      allowed_tlds: mockData.allowed_tlds,
    }
    render(<ChartJsTlds data={emptyData} />)
    expect(screen.getByText('No blocked parent domains data available')).toBeInTheDocument()
  })

  it('shows empty state for allowed TLDs when no data', () => {
    const emptyData = {
      blocked_tlds: mockData.blocked_tlds,
      allowed_tlds: [],
    }
    render(<ChartJsTlds data={emptyData} />)
    expect(screen.getByText('No allowed parent domains data available')).toBeInTheDocument()
  })

  it('handles null data gracefully', () => {
    render(<ChartJsTlds data={null} />)
    expect(screen.getByText('Top Blocked Parent Domains')).toBeInTheDocument()
    expect(screen.getByText('No blocked parent domains data available')).toBeInTheDocument()
    expect(screen.getByText('No allowed parent domains data available')).toBeInTheDocument()
  })

  it('displays most blocked parent domains summary', () => {
    render(<ChartJsTlds data={mockData} />)
    expect(screen.getByText('Most Blocked Parent Domains:')).toBeInTheDocument()
    expect(screen.getByText('.cn')).toBeInTheDocument()
    expect(screen.getByText('.xyz')).toBeInTheDocument()
    expect(screen.getByText('.ru')).toBeInTheDocument()
  })

  it('displays most requested parent domains summary', () => {
    render(<ChartJsTlds data={mockData} />)
    expect(screen.getByText('Most Requested Parent Domains:')).toBeInTheDocument()
    expect(screen.getByText('.com')).toBeInTheDocument()
    expect(screen.getByText('.net')).toBeInTheDocument()
    expect(screen.getByText('.org')).toBeInTheDocument()
  })

  it('formats TLD counts with locale strings', () => {
    render(<ChartJsTlds data={mockData} />)
    // Check that the counts are displayed with proper formatting (may appear multiple times)
    expect(screen.getAllByText('1,500').length).toBeGreaterThan(0)
    expect(screen.getAllByText('5,000').length).toBeGreaterThan(0)
  })

  it('only shows top 3 TLDs in summary', () => {
    const dataWithMany = {
      blocked_tlds: [
        { domain: '.tld1', count: 100, percentage: 10 },
        { domain: '.tld2', count: 90, percentage: 9 },
        { domain: '.tld3', count: 80, percentage: 8 },
        { domain: '.tld4', count: 70, percentage: 7 },
        { domain: '.tld5', count: 60, percentage: 6 },
      ],
      allowed_tlds: [],
    }
    render(<ChartJsTlds data={dataWithMany} />)
    
    // First 3 should be visible
    expect(screen.getByText('.tld1')).toBeInTheDocument()
    expect(screen.getByText('.tld2')).toBeInTheDocument()
    expect(screen.getByText('.tld3')).toBeInTheDocument()
    
    // 4th and 5th should not be in the summary
    expect(screen.queryByText('.tld4')).not.toBeInTheDocument()
    expect(screen.queryByText('.tld5')).not.toBeInTheDocument()
  })

  it('displays correct card titles', () => {
    render(<ChartJsTlds data={mockData} />)
    expect(screen.getByText('Blocked Parent Domains')).toBeInTheDocument()
    expect(screen.getByText('Allowed Parent Domains')).toBeInTheDocument()
    expect(screen.getByText('Total Blocked Requests')).toBeInTheDocument()
    expect(screen.getByText('Total Allowed Requests')).toBeInTheDocument()
  })

  it('shows summary section only when data exists', () => {
    const emptyData = {
      blocked_tlds: [],
      allowed_tlds: [],
    }
    const { container } = render(<ChartJsTlds data={emptyData} />)
    
    // Summary sections should not exist when no data
    expect(screen.queryByText('Most Blocked Parent Domains:')).not.toBeInTheDocument()
    expect(screen.queryByText('Most Requested Parent Domains:')).not.toBeInTheDocument()
  })
})
