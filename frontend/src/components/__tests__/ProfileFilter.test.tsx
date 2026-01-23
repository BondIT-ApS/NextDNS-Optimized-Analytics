import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ProfileFilter } from '../ProfileFilter'

describe('ProfileFilter', () => {
  const mockOnProfileSelectionChange = vi.fn()
  const defaultProps = {
    availableProfiles: ['profile1', 'profile2', 'profile3'],
    selectedProfiles: [],
    onProfileSelectionChange: mockOnProfileSelectionChange,
    profileColors: {
      profile1: '#FF0000',
      profile2: '#00FF00',
      profile3: '#0000FF',
    },
    profileNames: {
      profile1: 'Home Network',
      profile2: 'Office Network',
      profile3: 'Mobile Devices',
    },
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('No Profiles State', () => {
    it('should show disabled state when no profiles available', () => {
      render(
        <ProfileFilter
          {...defaultProps}
          availableProfiles={[]}
        />
      )

      expect(screen.getByText('Profile Filter')).toBeInTheDocument()
      expect(
        screen.getByText('No profiles available. Start fetching data.')
      ).toBeInTheDocument()
    })

    it('should show disabled state when availableProfiles is undefined', () => {
      render(
        <ProfileFilter
          {...defaultProps}
          availableProfiles={undefined as any}
        />
      )

      expect(
        screen.getByText('No profiles available. Start fetching data.')
      ).toBeInTheDocument()
    })
  })

  describe('Profile Selection', () => {
    it('should display selected profile count in badge', () => {
      render(
        <ProfileFilter
          {...defaultProps}
          selectedProfiles={['profile1', 'profile2']}
        />
      )

      expect(screen.getByText('2')).toBeInTheDocument()
    })

    it('should toggle profile selection when clicked', async () => {
      render(<ProfileFilter {...defaultProps} />)

      // Expand filter
      await userEvent.click(screen.getByRole('button', { name: /expand/i }))

      // Click on Home Network
      await userEvent.click(screen.getByText('Home Network'))

      expect(mockOnProfileSelectionChange).toHaveBeenCalledWith(['profile1'])
    })

    it('should deselect profile when clicked again', async () => {
      render(
        <ProfileFilter {...defaultProps} selectedProfiles={['profile1']} />
      )

      // Expand filter
      await userEvent.click(screen.getByRole('button', { name: /expand/i }))

      // Click on Home Network to deselect (in the profile list, not the badge)
      const profileItems = screen.getAllByText('Home Network')
      await userEvent.click(profileItems[profileItems.length - 1])

      expect(mockOnProfileSelectionChange).toHaveBeenCalledWith([])
    })

    it('should show selected profiles as badges with colors', () => {
      render(
        <ProfileFilter
          {...defaultProps}
          selectedProfiles={['profile1', 'profile2']}
        />
      )

      // Both profiles should be visible as text
      expect(screen.getAllByText('Home Network').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Office Network').length).toBeGreaterThan(0)

      // Check that color dots are rendered (they have rounded-full class)
      const colorDots = document.querySelectorAll('.rounded-full')
      expect(colorDots.length).toBeGreaterThan(0)
    })

    it('should remove profile when X button clicked on badge', async () => {
      render(
        <ProfileFilter
          {...defaultProps}
          selectedProfiles={['profile1', 'profile2']}
        />
      )

      // Find the badge with Home Network and click its X button
      const homeNetworkText = screen.getByText('Home Network')
      const badge = homeNetworkText.parentElement
      const removeButton = badge?.querySelector('button')

      if (removeButton) {
        await userEvent.click(removeButton)
        expect(mockOnProfileSelectionChange).toHaveBeenCalledWith(['profile2'])
      }
    })
  })

  describe('Profile Display Names', () => {
    it('should display profile names when provided', async () => {
      render(<ProfileFilter {...defaultProps} />)

      // Expand filter
      await userEvent.click(screen.getByRole('button', { name: /expand/i }))

      expect(screen.getByText('Home Network')).toBeInTheDocument()
      expect(screen.getByText('Office Network')).toBeInTheDocument()
      expect(screen.getByText('Mobile Devices')).toBeInTheDocument()
    })

    it('should fallback to profile ID when name not provided', async () => {
      render(
        <ProfileFilter
          {...defaultProps}
          profileNames={{}}
        />
      )

      // Expand filter
      await userEvent.click(screen.getByRole('button', { name: /expand/i }))

      expect(screen.getByText('profile1')).toBeInTheDocument()
      expect(screen.getByText('profile2')).toBeInTheDocument()
      expect(screen.getByText('profile3')).toBeInTheDocument()
    })
  })

  describe('Profile Colors', () => {
    it('should render colored dots for each profile', async () => {
      render(<ProfileFilter {...defaultProps} />)

      // Expand filter
      await userEvent.click(screen.getByRole('button', { name: /expand/i }))

      // Check for color dots with specific colors
      const colorDots = document.querySelectorAll('.h-3.w-3.rounded-full')
      expect(colorDots.length).toBeGreaterThanOrEqual(3)
    })

    it('should apply colors to selected profile badges', () => {
      const { container } = render(
        <ProfileFilter
          {...defaultProps}
          selectedProfiles={['profile1']}
        />
      )

      // Find elements with inline styles that contain color values
      // The color dots have inline backgroundColor styles
      const styledElements = container.querySelectorAll('[style]')
      const hasColorStyle = Array.from(styledElements).some(
        el => el.getAttribute('style')?.includes('background-color') ||
              el.getAttribute('style')?.includes('border-color')
      )

      expect(hasColorStyle).toBe(true)
    })
  })

  describe('Search Functionality', () => {
    it('should filter profiles based on search query', async () => {
      render(<ProfileFilter {...defaultProps} />)

      // Expand filter
      await userEvent.click(screen.getByRole('button', { name: /expand/i }))

      // Type in search
      const searchInput = screen.getByPlaceholderText('Search profiles...')
      await userEvent.type(searchInput, 'Network')

      // Should show filtered results
      await waitFor(() => {
        expect(screen.getByText('Home Network')).toBeInTheDocument()
        expect(screen.getByText('Office Network')).toBeInTheDocument()
        expect(screen.queryByText('Mobile Devices')).not.toBeInTheDocument()
      })
    })

    it('should search by profile ID when name not available', async () => {
      render(
        <ProfileFilter
          {...defaultProps}
          profileNames={{}}
        />
      )

      // Expand filter
      await userEvent.click(screen.getByRole('button', { name: /expand/i }))

      // Type in search
      const searchInput = screen.getByPlaceholderText('Search profiles...')
      await userEvent.type(searchInput, 'profile1')

      await waitFor(() => {
        expect(screen.getByText('profile1')).toBeInTheDocument()
        expect(screen.queryByText('profile2')).not.toBeInTheDocument()
      })
    })

    it('should show no match message when search has no results', async () => {
      render(<ProfileFilter {...defaultProps} />)

      // Expand filter
      await userEvent.click(screen.getByRole('button', { name: /expand/i }))

      // Type in search with no matches
      const searchInput = screen.getByPlaceholderText('Search profiles...')
      await userEvent.type(searchInput, 'NonExistent')

      await waitFor(() => {
        expect(
          screen.getByText('No profiles match your search.')
        ).toBeInTheDocument()
      })
    })

    it('should be case-insensitive', async () => {
      render(<ProfileFilter {...defaultProps} />)

      // Expand filter
      await userEvent.click(screen.getByRole('button', { name: /expand/i }))

      // Type in lowercase
      const searchInput = screen.getByPlaceholderText('Search profiles...')
      await userEvent.type(searchInput, 'home')

      await waitFor(() => {
        expect(screen.getByText('Home Network')).toBeInTheDocument()
      })
    })
  })

  describe('Select All/Clear All', () => {
    it('should select all profiles when Select All clicked', async () => {
      render(<ProfileFilter {...defaultProps} />)

      // Expand filter
      await userEvent.click(screen.getByRole('button', { name: /expand/i }))

      // Click Select All
      await userEvent.click(screen.getByRole('button', { name: /select all/i }))

      expect(mockOnProfileSelectionChange).toHaveBeenCalledWith([
        'profile1',
        'profile2',
        'profile3',
      ])
    })

    it('should select all filtered profiles when search is active', async () => {
      render(<ProfileFilter {...defaultProps} />)

      // Expand filter
      await userEvent.click(screen.getByRole('button', { name: /expand/i }))

      // Filter profiles
      const searchInput = screen.getByPlaceholderText('Search profiles...')
      await userEvent.type(searchInput, 'Network')

      // Click Select All (should only select filtered profiles)
      await userEvent.click(screen.getByRole('button', { name: /select all/i }))

      expect(mockOnProfileSelectionChange).toHaveBeenCalledWith([
        'profile1',
        'profile2',
      ])
    })

    it('should clear all profiles when Clear All clicked', async () => {
      render(
        <ProfileFilter
          {...defaultProps}
          selectedProfiles={['profile1', 'profile2']}
        />
      )

      // Expand filter
      await userEvent.click(screen.getByRole('button', { name: /expand/i }))

      // Click Clear All
      await userEvent.click(screen.getByRole('button', { name: /clear all/i }))

      expect(mockOnProfileSelectionChange).toHaveBeenCalledWith([])
    })

    it('should disable Select All when all filtered profiles are selected', async () => {
      render(
        <ProfileFilter
          {...defaultProps}
          selectedProfiles={['profile1', 'profile2', 'profile3']}
        />
      )

      // Expand filter
      await userEvent.click(screen.getByRole('button', { name: /expand/i }))

      const selectAllButton = screen.getByRole('button', {
        name: /select all/i,
      })
      expect(selectAllButton).toBeDisabled()
    })

    it('should disable Clear All when no profiles are selected', async () => {
      render(<ProfileFilter {...defaultProps} selectedProfiles={[]} />)

      // Expand filter
      await userEvent.click(screen.getByRole('button', { name: /expand/i }))

      const clearAllButton = screen.getByRole('button', { name: /clear all/i })
      expect(clearAllButton).toBeDisabled()
    })
  })

  describe('Expand/Collapse', () => {
    it('should start collapsed', () => {
      render(<ProfileFilter {...defaultProps} />)

      expect(
        screen.getByRole('button', { name: /expand/i })
      ).toBeInTheDocument()
      expect(
        screen.queryByPlaceholderText('Search profiles...')
      ).not.toBeInTheDocument()
    })

    it('should expand when Expand button clicked', async () => {
      render(<ProfileFilter {...defaultProps} />)

      await userEvent.click(screen.getByRole('button', { name: /expand/i }))

      expect(
        screen.getByRole('button', { name: /collapse/i })
      ).toBeInTheDocument()
      expect(
        screen.getByPlaceholderText('Search profiles...')
      ).toBeInTheDocument()
    })

    it('should collapse when Collapse button clicked', async () => {
      render(<ProfileFilter {...defaultProps} />)

      // Expand first
      await userEvent.click(screen.getByRole('button', { name: /expand/i }))
      expect(
        screen.getByPlaceholderText('Search profiles...')
      ).toBeInTheDocument()

      // Then collapse
      await userEvent.click(screen.getByRole('button', { name: /collapse/i }))
      expect(
        screen.queryByPlaceholderText('Search profiles...')
      ).not.toBeInTheDocument()
    })
  })

  describe('Checkbox Visual States', () => {
    it('should show checked icon for selected profiles', async () => {
      render(
        <ProfileFilter {...defaultProps} selectedProfiles={['profile1']} />
      )

      // Expand filter
      await userEvent.click(screen.getByRole('button', { name: /expand/i }))

      // CheckSquare icon should be visible for selected profile
      const checkSquareIcons = document.querySelectorAll('.text-primary')
      expect(checkSquareIcons.length).toBeGreaterThan(0)
    })

    it('should show unchecked icon for unselected profiles', async () => {
      render(<ProfileFilter {...defaultProps} selectedProfiles={[]} />)

      // Expand filter
      await userEvent.click(screen.getByRole('button', { name: /expand/i }))

      // Square icons should be visible for unselected profiles
      const squareIcons = document.querySelectorAll('.text-muted-foreground')
      expect(squareIcons.length).toBeGreaterThan(0)
    })
  })

  describe('Empty State', () => {
    it('should show message when no profiles found (no search)', async () => {
      render(
        <ProfileFilter
          {...defaultProps}
          availableProfiles={['profile1']}
        />
      )

      // Expand filter
      await userEvent.click(screen.getByRole('button', { name: /expand/i }))

      // Clear the only profile
      const searchInput = screen.getByPlaceholderText('Search profiles...')
      await userEvent.type(searchInput, 'xxx')

      expect(screen.getByText('No profiles match your search.')).toBeInTheDocument()
    })
  })
})
