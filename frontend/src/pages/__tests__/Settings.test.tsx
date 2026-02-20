import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Settings } from '../Settings'

// Mock the API client so no real HTTP calls are made
vi.mock('@/services/api', () => ({
  apiClient: {
    getNextDNSApiKey: vi.fn().mockResolvedValue({
      configured: true,
      masked_key: '••••1234',
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
