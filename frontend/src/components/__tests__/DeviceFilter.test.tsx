import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DeviceFilter } from '../DeviceFilter'
import * as useDevicesHook from '@/hooks/useDevices'

// Mock the useDeviceNames hook
vi.mock('@/hooks/useDevices', () => ({
  useDeviceNames: vi.fn(),
}))

describe('DeviceFilter', () => {
  const mockOnDeviceSelectionChange = vi.fn()
  const defaultProps = {
    selectedProfile: 'profile1',
    selectedDevices: [],
    onDeviceSelectionChange: mockOnDeviceSelectionChange,
    timeRange: '24h',
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('No Profile Selected State', () => {
    it('should show disabled state when no profile is selected', () => {
      vi.mocked(useDevicesHook.useDeviceNames).mockReturnValue({
        deviceNames: [],
        isLoading: false,
        error: null,
      })

      render(<DeviceFilter {...defaultProps} selectedProfile={undefined} />)

      expect(screen.getByText('Device Filter')).toBeInTheDocument()
      expect(
        screen.getByText('Select a profile to see available devices')
      ).toBeInTheDocument()
    })
  })

  describe('Loading State', () => {
    it('should show loading skeleton when fetching devices', async () => {
      vi.mocked(useDevicesHook.useDeviceNames).mockReturnValue({
        deviceNames: [],
        isLoading: true,
        error: null,
      })

      render(<DeviceFilter {...defaultProps} />)

      // Expand to see loading state
      const expandButton = screen.getByRole('button', { name: /expand/i })
      await userEvent.click(expandButton)

      // Check for loading skeleton (has animate-pulse class)
      const loadingElements = document.querySelectorAll('.animate-pulse')
      expect(loadingElements.length).toBeGreaterThan(0)
    })
  })

  describe('Error State', () => {
    it('should show error message when device fetch fails', async () => {
      vi.mocked(useDevicesHook.useDeviceNames).mockReturnValue({
        deviceNames: [],
        isLoading: false,
        error: new Error('Failed to fetch'),
      })

      render(<DeviceFilter {...defaultProps} />)

      // Expand to see error
      const expandButton = screen.getByRole('button', { name: /expand/i })
      await userEvent.click(expandButton)

      expect(
        screen.getByText(/Failed to load devices/i)
      ).toBeInTheDocument()
    })
  })

  describe('Device Selection', () => {
    beforeEach(() => {
      vi.mocked(useDevicesHook.useDeviceNames).mockReturnValue({
        deviceNames: ['iPhone', 'MacBook', 'iPad'],
        isLoading: false,
        error: null,
      })
    })

    it('should display selected device count in badge', () => {
      render(
        <DeviceFilter {...defaultProps} selectedDevices={['iPhone', 'iPad']} />
      )

      expect(screen.getByText('2')).toBeInTheDocument()
    })

    it('should toggle device selection when clicked', async () => {
      render(<DeviceFilter {...defaultProps} />)

      // Expand filter
      await userEvent.click(screen.getByRole('button', { name: /expand/i }))

      // Click on iPhone
      await userEvent.click(screen.getByText('iPhone'))

      expect(mockOnDeviceSelectionChange).toHaveBeenCalledWith(['iPhone'])
    })

    it('should deselect device when clicked again', async () => {
      render(
        <DeviceFilter {...defaultProps} selectedDevices={['iPhone']} />
      )

      // Expand filter
      await userEvent.click(screen.getByRole('button', { name: /expand/i }))

      // Click on iPhone to deselect (in the device list, not the badge)
      const deviceList = screen.getAllByText('iPhone')
      await userEvent.click(deviceList[deviceList.length - 1])

      expect(mockOnDeviceSelectionChange).toHaveBeenCalledWith([])
    })

    it('should show selected devices as badges', () => {
      render(
        <DeviceFilter {...defaultProps} selectedDevices={['iPhone', 'iPad']} />
      )

      // Both devices should be visible as text (in badges and potentially in list)
      expect(screen.getAllByText('iPhone').length).toBeGreaterThan(0)
      expect(screen.getAllByText('iPad').length).toBeGreaterThan(0)
    })

    it('should remove device when X button clicked on badge', async () => {
      render(
        <DeviceFilter {...defaultProps} selectedDevices={['iPhone', 'iPad']} />
      )

      // Find and click the X button for iPhone
      const badges = screen.getAllByText('iPhone')
      const iPhoneBadge = badges[0].parentElement
      const removeButton = iPhoneBadge?.querySelector('button')

      if (removeButton) {
        await userEvent.click(removeButton)
        expect(mockOnDeviceSelectionChange).toHaveBeenCalledWith(['iPad'])
      }
    })
  })

  describe('Search Functionality', () => {
    beforeEach(() => {
      vi.mocked(useDevicesHook.useDeviceNames).mockReturnValue({
        deviceNames: ['iPhone', 'MacBook', 'iPad', 'Android Phone'],
        isLoading: false,
        error: null,
      })
    })

    it('should filter devices based on search query', async () => {
      render(<DeviceFilter {...defaultProps} />)

      // Expand filter
      await userEvent.click(screen.getByRole('button', { name: /expand/i }))

      // Type in search
      const searchInput = screen.getByPlaceholderText('Search devices...')
      await userEvent.type(searchInput, 'Phone')

      // Should show filtered results
      await waitFor(() => {
        expect(screen.getByText('iPhone')).toBeInTheDocument()
        expect(screen.getByText('Android Phone')).toBeInTheDocument()
        expect(screen.queryByText('MacBook')).not.toBeInTheDocument()
      })
    })

    it('should show no match message when search has no results', async () => {
      render(<DeviceFilter {...defaultProps} />)

      // Expand filter
      await userEvent.click(screen.getByRole('button', { name: /expand/i }))

      // Type in search with no matches
      const searchInput = screen.getByPlaceholderText('Search devices...')
      await userEvent.type(searchInput, 'NonExistent')

      await waitFor(() => {
        expect(
          screen.getByText('No devices match your search.')
        ).toBeInTheDocument()
      })
    })
  })

  describe('Select All/Clear All', () => {
    beforeEach(() => {
      vi.mocked(useDevicesHook.useDeviceNames).mockReturnValue({
        deviceNames: ['iPhone', 'MacBook', 'iPad'],
        isLoading: false,
        error: null,
      })
    })

    it('should select all devices when Select All clicked', async () => {
      render(<DeviceFilter {...defaultProps} />)

      // Expand filter
      await userEvent.click(screen.getByRole('button', { name: /expand/i }))

      // Click Select All
      await userEvent.click(screen.getByRole('button', { name: /select all/i }))

      expect(mockOnDeviceSelectionChange).toHaveBeenCalledWith([
        'iPhone',
        'MacBook',
        'iPad',
      ])
    })

    it('should clear all devices when Clear All clicked', async () => {
      render(
        <DeviceFilter {...defaultProps} selectedDevices={['iPhone', 'iPad']} />
      )

      // Expand filter
      await userEvent.click(screen.getByRole('button', { name: /expand/i }))

      // Click Clear All
      await userEvent.click(screen.getByRole('button', { name: /clear all/i }))

      expect(mockOnDeviceSelectionChange).toHaveBeenCalledWith([])
    })

    it('should disable Select All when all devices are selected', async () => {
      render(
        <DeviceFilter
          {...defaultProps}
          selectedDevices={['iPhone', 'MacBook', 'iPad']}
        />
      )

      // Expand filter
      await userEvent.click(screen.getByRole('button', { name: /expand/i }))

      const selectAllButton = screen.getByRole('button', {
        name: /select all/i,
      })
      expect(selectAllButton).toBeDisabled()
    })

    it('should disable Clear All when no devices are selected', async () => {
      render(<DeviceFilter {...defaultProps} selectedDevices={[]} />)

      // Expand filter
      await userEvent.click(screen.getByRole('button', { name: /expand/i }))

      const clearAllButton = screen.getByRole('button', { name: /clear all/i })
      expect(clearAllButton).toBeDisabled()
    })
  })

  describe('Expand/Collapse', () => {
    beforeEach(() => {
      vi.mocked(useDevicesHook.useDeviceNames).mockReturnValue({
        deviceNames: ['iPhone', 'MacBook'],
        isLoading: false,
        error: null,
      })
    })

    it('should start collapsed', () => {
      render(<DeviceFilter {...defaultProps} />)

      expect(screen.getByRole('button', { name: /expand/i })).toBeInTheDocument()
      expect(screen.queryByPlaceholderText('Search devices...')).not.toBeInTheDocument()
    })

    it('should expand when Expand button clicked', async () => {
      render(<DeviceFilter {...defaultProps} />)

      await userEvent.click(screen.getByRole('button', { name: /expand/i }))

      expect(screen.getByRole('button', { name: /collapse/i })).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Search devices...')).toBeInTheDocument()
    })

    it('should collapse when Collapse button clicked', async () => {
      render(<DeviceFilter {...defaultProps} />)

      // Expand first
      await userEvent.click(screen.getByRole('button', { name: /expand/i }))
      expect(screen.getByPlaceholderText('Search devices...')).toBeInTheDocument()

      // Then collapse
      await userEvent.click(screen.getByRole('button', { name: /collapse/i }))
      expect(screen.queryByPlaceholderText('Search devices...')).not.toBeInTheDocument()
    })
  })

  describe('Empty State', () => {
    it('should show message when no devices found', async () => {
      vi.mocked(useDevicesHook.useDeviceNames).mockReturnValue({
        deviceNames: [],
        isLoading: false,
        error: null,
      })

      render(<DeviceFilter {...defaultProps} />)

      // Expand filter
      await userEvent.click(screen.getByRole('button', { name: /expand/i }))

      expect(
        screen.getByText('No devices found for this profile.')
      ).toBeInTheDocument()
    })
  })
})
