import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  Skeleton,
  DashboardCardSkeleton,
  SystemResourceCardSkeleton,
  SystemInfoSkeleton,
  LoadingSpinner,
  LoadingState,
  ErrorState,
  ConnectionIndicator,
  RetryIndicator,
  OfflineBanner,
  DataFreshnessIndicator,
} from '../LoadingSkeletons'

describe('LoadingSkeletons', () => {
  describe('Skeleton', () => {
    it('renders with default className', () => {
      const { container } = render(<Skeleton />)
      const skeleton = container.querySelector('.animate-pulse')
      expect(skeleton).toBeInTheDocument()
      expect(skeleton).toHaveClass('bg-muted', 'rounded')
    })

    it('renders with custom className', () => {
      const { container } = render(<Skeleton className="h-4 w-20" />)
      const skeleton = container.querySelector('.animate-pulse')
      expect(skeleton).toHaveClass('h-4', 'w-20')
    })
  })

  describe('DashboardCardSkeleton', () => {
    it('renders skeleton card structure', () => {
      const { container } = render(<DashboardCardSkeleton />)
      expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
    })
  })

  describe('SystemResourceCardSkeleton', () => {
    it('renders system resource card skeleton', () => {
      const { container } = render(<SystemResourceCardSkeleton />)
      expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
    })
  })

  describe('SystemInfoSkeleton', () => {
    it('renders system info skeleton with backend and frontend sections', () => {
      const { container } = render(<SystemInfoSkeleton />)
      expect(container.querySelector('.animate-pulse')).toBeInTheDocument()

      // Should have 5 backend items and 6 frontend items
      const skeletonItems = container.querySelectorAll('.animate-pulse .h-4')
      expect(skeletonItems.length).toBeGreaterThan(0)
    })
  })

  describe('LoadingSpinner', () => {
    it('renders with medium size by default', () => {
      const { container } = render(<LoadingSpinner />)
      const spinner = container.querySelector('.animate-spin')
      expect(spinner).toBeInTheDocument()
      expect(spinner).toHaveClass('h-6', 'w-6')
    })

    it('renders with small size', () => {
      const { container } = render(<LoadingSpinner size="small" />)
      const spinner = container.querySelector('.animate-spin')
      expect(spinner).toHaveClass('h-4', 'w-4')
    })

    it('renders with large size', () => {
      const { container } = render(<LoadingSpinner size="large" />)
      const spinner = container.querySelector('.animate-spin')
      expect(spinner).toHaveClass('h-8', 'w-8')
    })
  })

  describe('LoadingState', () => {
    it('renders with default message and spinner', () => {
      render(<LoadingState />)
      expect(screen.getByText('Loading...')).toBeInTheDocument()
    })

    it('renders with custom message', () => {
      render(<LoadingState message="Fetching data..." />)
      expect(screen.getByText('Fetching data...')).toBeInTheDocument()
    })

    it('renders without spinner when showSpinner is false', () => {
      const { container } = render(<LoadingState showSpinner={false} />)
      expect(container.querySelector('.animate-spin')).not.toBeInTheDocument()
    })

    it('applies custom className', () => {
      const { container } = render(<LoadingState className="my-custom-class" />)
      expect(container.querySelector('.my-custom-class')).toBeInTheDocument()
    })
  })

  describe('ErrorState', () => {
    it('renders with default message', () => {
      render(<ErrorState />)
      expect(screen.getByText('Oops!')).toBeInTheDocument()
      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    })

    it('renders with custom message', () => {
      render(<ErrorState message="Network error occurred" />)
      expect(screen.getByText('Network error occurred')).toBeInTheDocument()
    })

    it('renders retry button when onRetry is provided', async () => {
      const handleRetry = vi.fn()
      const user = userEvent.setup()

      render(<ErrorState onRetry={handleRetry} />)
      const retryButton = screen.getByRole('button', { name: /try again/i })
      expect(retryButton).toBeInTheDocument()

      await user.click(retryButton)
      expect(handleRetry).toHaveBeenCalledTimes(1)
    })

    it('does not render retry button when showRetryButton is false', () => {
      const handleRetry = vi.fn()
      render(<ErrorState onRetry={handleRetry} showRetryButton={false} />)
      expect(
        screen.queryByRole('button', { name: /try again/i })
      ).not.toBeInTheDocument()
    })

    it('does not render retry button when onRetry is not provided', () => {
      render(<ErrorState />)
      expect(
        screen.queryByRole('button', { name: /try again/i })
      ).not.toBeInTheDocument()
    })
  })

  describe('ConnectionIndicator', () => {
    it('shows loading state when isLoading is true', () => {
      render(<ConnectionIndicator isConnected={false} isLoading={true} />)
      expect(screen.getByText('Checking...')).toBeInTheDocument()
    })

    it('shows connected state', () => {
      render(<ConnectionIndicator isConnected={true} />)
      expect(screen.getByText('Connected')).toBeInTheDocument()
    })

    it('shows disconnected state', () => {
      render(<ConnectionIndicator isConnected={false} />)
      expect(screen.getByText('Disconnected')).toBeInTheDocument()
    })
  })

  describe('RetryIndicator', () => {
    it('returns null when not retrying and retryCount is 0', () => {
      const { container } = render(
        <RetryIndicator isRetrying={false} retryCount={0} maxRetries={3} />
      )
      expect(container.firstChild).toBeNull()
    })

    it('shows retrying state', () => {
      render(<RetryIndicator isRetrying={true} retryCount={2} maxRetries={5} />)
      expect(screen.getByText(/Retrying... \(2\/5\)/)).toBeInTheDocument()
    })

    it('shows retry count when not currently retrying', () => {
      render(
        <RetryIndicator isRetrying={false} retryCount={3} maxRetries={5} />
      )
      expect(screen.getByText(/Retried 3 times/)).toBeInTheDocument()
    })

    it('shows next retry countdown', () => {
      render(
        <RetryIndicator
          isRetrying={true}
          retryCount={1}
          maxRetries={3}
          nextRetryIn={5}
        />
      )
      expect(screen.getByText(/Next retry in 5s/)).toBeInTheDocument()
    })
  })

  describe('OfflineBanner', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })

    afterEach(() => {
      vi.restoreAllMocks()
      vi.useRealTimers()
    })

    it('returns null when not offline', () => {
      const { container } = render(<OfflineBanner isOffline={false} />)
      expect(container.firstChild).toBeNull()
    })

    it('shows offline mode banner', () => {
      render(<OfflineBanner isOffline={true} />)
      expect(screen.getByText('Offline Mode')).toBeInTheDocument()
    })

    it('shows time since last update', () => {
      const lastUpdated = Date.now() - 60000 // 1 minute ago
      render(<OfflineBanner isOffline={true} lastUpdated={lastUpdated} />)
      expect(screen.getByText(/1m 0s ago/)).toBeInTheDocument()
    })

    it('renders with live age updates', () => {
      const lastUpdated = Date.now() - 5000 // 5 seconds ago
      render(<OfflineBanner isOffline={true} lastUpdated={lastUpdated} />)

      // Should show initial age
      expect(screen.getByText(/\ds ago/)).toBeInTheDocument()
    })
  })

  describe('DataFreshnessIndicator', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })

    afterEach(() => {
      vi.restoreAllMocks()
      vi.useRealTimers()
    })

    it('returns null when loading', () => {
      const { container } = render(
        <DataFreshnessIndicator isFromCache={false} isLoading={true} />
      )
      expect(container.firstChild).toBeNull()
    })

    it('returns null when not from cache and no lastUpdated', () => {
      const { container } = render(
        <DataFreshnessIndicator isFromCache={false} isLoading={false} />
      )
      expect(container.firstChild).toBeNull()
    })

    it('shows cached data age', () => {
      const lastUpdated = Date.now() - 30000 // 30 seconds ago
      render(
        <DataFreshnessIndicator isFromCache={true} lastUpdated={lastUpdated} />
      )
      expect(screen.getByText(/Cached 30s ago/)).toBeInTheDocument()
    })

    it('shows updated data age', () => {
      const lastUpdated = Date.now() - 45000 // 45 seconds ago
      render(
        <DataFreshnessIndicator isFromCache={false} lastUpdated={lastUpdated} />
      )
      expect(screen.getByText(/Updated 45s ago/)).toBeInTheDocument()
    })

    it('renders with live age updates', () => {
      const lastUpdated = Date.now() - 10000 // 10 seconds ago
      render(
        <DataFreshnessIndicator isFromCache={true} lastUpdated={lastUpdated} />
      )

      // Should show cached age text
      expect(screen.getByText(/Cached \d+s ago/)).toBeInTheDocument()
    })

    it('formats time correctly for different durations', () => {
      const testCases = [
        { age: 5000, expected: /5s ago/ },
        { age: 90000, expected: /1m 30s ago/ },
        { age: 3600000, expected: /1h 0m ago/ },
        { age: 90000000, expected: /1d 1h ago/ },
      ]

      testCases.forEach(({ age, expected }) => {
        const lastUpdated = Date.now() - age
        const { rerender } = render(
          <DataFreshnessIndicator
            isFromCache={true}
            lastUpdated={lastUpdated}
          />
        )
        expect(screen.getByText(expected)).toBeInTheDocument()
        rerender(<div />) // Clean up before next iteration
      })
    })
  })
})
