import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DomainExclusionInput, COMPANY_PRESETS } from '../DomainExclusionInput'

// 🧱 DomainExclusionInput Component Tests
// Validates preset buttons, pattern input, and validation bricks

describe('🧱 DomainExclusionInput Component', () => {
  const mockOnChange = vi.fn()
  const defaultProps = {
    value: [] as string[],
    onChange: mockOnChange,
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Quick Exclude Presets', () => {
    it('should render the Quick Exclude Companies toggle button', () => {
      render(<DomainExclusionInput {...defaultProps} />)

      expect(screen.getByText('Quick Exclude Companies')).toBeInTheDocument()
    })

    it('should show preset buttons when toggle is clicked', async () => {
      const user = userEvent.setup()
      render(<DomainExclusionInput {...defaultProps} />)

      await user.click(screen.getByText('Quick Exclude Companies'))

      expect(screen.getByText('Apple')).toBeInTheDocument()
      expect(screen.getByText('Google')).toBeInTheDocument()
      expect(screen.getByText('Microsoft')).toBeInTheDocument()
      expect(screen.getByText('Meta')).toBeInTheDocument()
      expect(screen.getByText('Snapchat')).toBeInTheDocument()
      expect(screen.getByText('Amazon')).toBeInTheDocument()
      expect(screen.getByText('Netflix')).toBeInTheDocument()
      expect(screen.getByText('TikTok')).toBeInTheDocument()
    })

    it('should hide preset buttons when toggle is clicked again', async () => {
      const user = userEvent.setup()
      render(<DomainExclusionInput {...defaultProps} />)

      // Open
      await user.click(screen.getByText('Quick Exclude Companies'))
      expect(screen.getByText('Apple')).toBeInTheDocument()

      // Close
      await user.click(screen.getByText('Quick Exclude Companies'))
      expect(screen.queryByText('Apple')).not.toBeInTheDocument()
    })

    it('should add all preset patterns when clicking an inactive preset', async () => {
      const user = userEvent.setup()
      render(<DomainExclusionInput {...defaultProps} />)

      await user.click(screen.getByText('Quick Exclude Companies'))
      await user.click(screen.getByText('Snapchat'))

      expect(mockOnChange).toHaveBeenCalledWith([
        '*.snapchat.com',
        '*.sc-gw.com',
        '*.snap-dev.net',
        '*.snapkit.co',
      ])
    })

    it('should only add missing patterns when preset is partially active', async () => {
      const user = userEvent.setup()
      render(
        <DomainExclusionInput
          {...defaultProps}
          value={['*.snapchat.com', '*.sc-gw.com']}
        />
      )

      await user.click(screen.getByText('Quick Exclude Companies'))
      await user.click(screen.getByText('Snapchat'))

      // Should append only the missing patterns
      expect(mockOnChange).toHaveBeenCalledWith([
        '*.snapchat.com',
        '*.sc-gw.com',
        '*.snap-dev.net',
        '*.snapkit.co',
      ])
    })

    it('should remove all preset patterns when clicking a fully active preset', async () => {
      const user = userEvent.setup()
      const snapchatPatterns = [
        '*.snapchat.com',
        '*.sc-gw.com',
        '*.snap-dev.net',
        '*.snapkit.co',
      ]
      render(
        <DomainExclusionInput
          {...defaultProps}
          value={[...snapchatPatterns, '*.custom-domain.com']}
        />
      )

      await user.click(screen.getByText('Quick Exclude Companies'))
      await user.click(screen.getByText('Snapchat'))

      // Should only keep the non-Snapchat pattern
      expect(mockOnChange).toHaveBeenCalledWith(['*.custom-domain.com'])
    })

    it('should show "partial" label when preset is partially active', async () => {
      const user = userEvent.setup()
      render(
        <DomainExclusionInput {...defaultProps} value={['*.snapchat.com']} />
      )

      await user.click(screen.getByText('Quick Exclude Companies'))

      expect(screen.getByText('partial')).toBeInTheDocument()
    })

    it('should not show "partial" label when preset is fully active', async () => {
      const user = userEvent.setup()
      render(
        <DomainExclusionInput
          {...defaultProps}
          value={[
            '*.snapchat.com',
            '*.sc-gw.com',
            '*.snap-dev.net',
            '*.snapkit.co',
          ]}
        />
      )

      await user.click(screen.getByText('Quick Exclude Companies'))

      expect(screen.queryByText('partial')).not.toBeInTheDocument()
    })
  })

  describe('Pattern Input', () => {
    it('should add pattern via Enter key', async () => {
      const user = userEvent.setup()
      render(<DomainExclusionInput {...defaultProps} />)

      const input = screen.getByPlaceholderText(
        'Enter domain pattern (e.g., *.apple.com)'
      )
      await user.type(input, '*.example.com{Enter}')

      expect(mockOnChange).toHaveBeenCalledWith(['*.example.com'])
    })

    it('should add pattern via Add button click', async () => {
      const user = userEvent.setup()
      render(<DomainExclusionInput {...defaultProps} />)

      const input = screen.getByPlaceholderText(
        'Enter domain pattern (e.g., *.apple.com)'
      )
      await user.type(input, '*.example.com')
      await user.click(screen.getByTitle('Add pattern'))

      expect(mockOnChange).toHaveBeenCalledWith(['*.example.com'])
    })

    it('should clear input via Escape key', async () => {
      const user = userEvent.setup()
      render(<DomainExclusionInput {...defaultProps} />)

      const input = screen.getByPlaceholderText(
        'Enter domain pattern (e.g., *.apple.com)'
      ) as HTMLInputElement
      await user.type(input, '*.example.com')
      expect(input.value).toBe('*.example.com')

      await user.keyboard('{Escape}')
      expect(input.value).toBe('')
    })

    it('should format pattern to lowercase', async () => {
      const user = userEvent.setup()
      render(<DomainExclusionInput {...defaultProps} />)

      const input = screen.getByPlaceholderText(
        'Enter domain pattern (e.g., *.apple.com)'
      )
      await user.type(input, '*.EXAMPLE.COM{Enter}')

      expect(mockOnChange).toHaveBeenCalledWith(['*.example.com'])
    })
  })

  describe('Pattern Validation', () => {
    it('should reject empty pattern', async () => {
      const user = userEvent.setup()
      render(
        <DomainExclusionInput {...defaultProps} value={['*.existing.com']} />
      )

      const input = screen.getByPlaceholderText(
        'Enter domain pattern (e.g., *.apple.com)'
      )
      // Type a space then clear to trigger empty validation
      await user.type(input, ' {Enter}')

      expect(screen.getByText('Pattern cannot be empty')).toBeInTheDocument()
      expect(mockOnChange).not.toHaveBeenCalled()
    })

    it('should reject overly broad patterns', async () => {
      const user = userEvent.setup()
      render(<DomainExclusionInput {...defaultProps} />)

      const input = screen.getByPlaceholderText(
        'Enter domain pattern (e.g., *.apple.com)'
      )

      await user.type(input, '*{Enter}')
      expect(
        screen.getByText('Pattern too broad - please be more specific')
      ).toBeInTheDocument()
    })

    it('should reject patterns with invalid characters', async () => {
      const user = userEvent.setup()
      render(<DomainExclusionInput {...defaultProps} />)

      const input = screen.getByPlaceholderText(
        'Enter domain pattern (e.g., *.apple.com)'
      )
      await user.type(input, '*.exam ple.com{Enter}')

      expect(
        screen.getByText('Pattern contains invalid characters')
      ).toBeInTheDocument()
    })

    it('should reject consecutive wildcards', async () => {
      const user = userEvent.setup()
      render(<DomainExclusionInput {...defaultProps} />)

      const input = screen.getByPlaceholderText(
        'Enter domain pattern (e.g., *.apple.com)'
      )
      await user.type(input, '**.example.com{Enter}')

      expect(
        screen.getByText('Consecutive wildcards not allowed')
      ).toBeInTheDocument()
    })

    it('should reject duplicate patterns', async () => {
      const user = userEvent.setup()
      render(
        <DomainExclusionInput {...defaultProps} value={['*.example.com']} />
      )

      const input = screen.getByPlaceholderText(
        'Enter domain pattern (e.g., *.apple.com)'
      )
      await user.type(input, '*.example.com{Enter}')

      expect(screen.getByText('Pattern already exists')).toBeInTheDocument()
    })

    it('should clear error when input changes', async () => {
      const user = userEvent.setup()
      render(<DomainExclusionInput {...defaultProps} />)

      const input = screen.getByPlaceholderText(
        'Enter domain pattern (e.g., *.apple.com)'
      )

      // Trigger an error
      await user.type(input, '*{Enter}')
      expect(
        screen.getByText('Pattern too broad - please be more specific')
      ).toBeInTheDocument()

      // Clear the input and type something new — error should disappear
      await user.clear(input)
      await user.type(input, 'a')
      expect(
        screen.queryByText('Pattern too broad - please be more specific')
      ).not.toBeInTheDocument()
    })
  })

  describe('Pattern Badges', () => {
    it('should display active patterns as badges', () => {
      render(
        <DomainExclusionInput
          {...defaultProps}
          value={['*.apple.com', '*.google.com']}
        />
      )

      expect(screen.getByText('*.apple.com')).toBeInTheDocument()
      expect(screen.getByText('*.google.com')).toBeInTheDocument()
    })

    it('should remove pattern when badge X button is clicked', async () => {
      const user = userEvent.setup()
      render(
        <DomainExclusionInput
          {...defaultProps}
          value={['*.apple.com', '*.google.com']}
        />
      )

      const removeButton = screen.getByLabelText(
        'Remove exclusion pattern *.apple.com'
      )
      await user.click(removeButton)

      expect(mockOnChange).toHaveBeenCalledWith(['*.google.com'])
    })

    it('should not display badges section when no patterns active', () => {
      render(<DomainExclusionInput {...defaultProps} value={[]} />)

      expect(screen.queryByText('patterns active')).not.toBeInTheDocument()
    })
  })

  describe('Pattern Count', () => {
    it('should show singular "pattern" for 1 active pattern', () => {
      render(<DomainExclusionInput {...defaultProps} value={['*.apple.com']} />)

      expect(screen.getByText('1 pattern active')).toBeInTheDocument()
    })

    it('should show plural "patterns" for multiple active patterns', () => {
      render(
        <DomainExclusionInput
          {...defaultProps}
          value={['*.apple.com', '*.google.com', '*.meta.com']}
        />
      )

      expect(screen.getByText('3 patterns active')).toBeInTheDocument()
    })
  })

  describe('Help Section', () => {
    it('should toggle help section when help button is clicked', async () => {
      const user = userEvent.setup()
      render(<DomainExclusionInput {...defaultProps} />)

      // Help should not be visible initially
      expect(
        screen.queryByText('Wildcard Pattern Examples:')
      ).not.toBeInTheDocument()

      // Click help button
      await user.click(screen.getByTitle('Show pattern help'))
      expect(screen.getByText('Wildcard Pattern Examples:')).toBeInTheDocument()

      // Click again to hide
      await user.click(screen.getByTitle('Show pattern help'))
      expect(
        screen.queryByText('Wildcard Pattern Examples:')
      ).not.toBeInTheDocument()
    })
  })
})

describe('🧱 COMPANY_PRESETS Data Validation', () => {
  it('should contain exactly 8 company presets', () => {
    expect(COMPANY_PRESETS).toHaveLength(8)
  })

  it('should have non-empty name, emoji, and patterns for every preset', () => {
    for (const preset of COMPANY_PRESETS) {
      expect(preset.name).toBeTruthy()
      expect(preset.emoji).toBeTruthy()
      expect(preset.patterns.length).toBeGreaterThan(0)
    }
  })

  it('should have all expected companies', () => {
    const names = COMPANY_PRESETS.map(p => p.name)
    expect(names).toEqual([
      'Apple',
      'Google',
      'Microsoft',
      'Meta',
      'Snapchat',
      'Amazon',
      'Netflix',
      'TikTok',
    ])
  })

  it('should have valid domain patterns (no empty strings)', () => {
    for (const preset of COMPANY_PRESETS) {
      for (const pattern of preset.patterns) {
        expect(pattern.trim().length).toBeGreaterThan(0)
      }
    }
  })

  it('should not have duplicate patterns across companies', () => {
    const allPatterns = COMPANY_PRESETS.flatMap(p => p.patterns)
    const uniquePatterns = new Set(allPatterns)
    expect(allPatterns.length).toBe(uniquePatterns.size)
  })

  it('should not have duplicate patterns within a single company', () => {
    for (const preset of COMPANY_PRESETS) {
      const unique = new Set(preset.patterns)
      expect(preset.patterns.length).toBe(unique.size)
    }
  })
})
