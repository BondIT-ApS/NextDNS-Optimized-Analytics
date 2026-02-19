import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Settings } from '../Settings'

// Mock the API client so no real HTTP calls are made
vi.mock('@/services/api', () => ({
  apiClient: {
    getNextDNSApiKey: vi.fn().mockResolvedValue({
      api_key_masked: '••••1234',
      api_key_configured: true,
    }),
    getNextDNSProfiles: vi.fn().mockResolvedValue({
      profiles: [],
      total: 0,
    }),
    getSystemSettings: vi.fn().mockResolvedValue({
      fetch_interval: 60,
      fetch_limit: 100,
      log_level: 'INFO',
    }),
  },
}))

describe('🧱 Settings Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render the page title', () => {
    render(<Settings />)
    expect(screen.getByText('Settings')).toBeInTheDocument()
  })

  it('should render the page description', () => {
    render(<Settings />)
    expect(
      screen.getByText(/Manage NextDNS configuration, profiles, and system behaviour/)
    ).toBeInTheDocument()
  })

  it('should render the NextDNS API Key card', () => {
    render(<Settings />)
    expect(screen.getByText('NextDNS API Key')).toBeInTheDocument()
  })

  it('should render the Profile Management card', () => {
    render(<Settings />)
    expect(screen.getByText('Profile Management')).toBeInTheDocument()
  })

  it('should render the System Settings card', () => {
    render(<Settings />)
    expect(screen.getByText('System Settings')).toBeInTheDocument()
  })
})
