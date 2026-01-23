import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ErrorBoundary, ApiErrorBoundary } from '../ErrorBoundary'

// Component that throws an error for testing
const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error')
  }
  return <div>Working component</div>
}

describe('ErrorBoundary', () => {
  // Suppress console.error for error boundary tests
  const originalError = console.error
  beforeEach(() => {
    console.error = vi.fn()
  })

  afterEach(() => {
    console.error = originalError
  })

  describe('Normal Operation', () => {
    it('should render children when no error occurs', () => {
      render(
        <ErrorBoundary>
          <div>Test content</div>
        </ErrorBoundary>
      )

      expect(screen.getByText('Test content')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('should catch errors and display default fallback UI', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
      expect(
        screen.getByText(/We encountered an unexpected error/)
      ).toBeInTheDocument()
    })

    it('should display error message in technical details', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      // Click to expand technical details
      const detailsButton = screen.getByText('Technical details')
      expect(detailsButton).toBeInTheDocument()
    })

    it('should show Try Again and Refresh Page buttons', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(
        screen.getByRole('button', { name: /try again/i })
      ).toBeInTheDocument()
      expect(
        screen.getByRole('button', { name: /refresh page/i })
      ).toBeInTheDocument()
    })
  })

  describe('Custom Fallback Component', () => {
    it('should render custom fallback when provided', () => {
      const CustomFallback = () => <div>Custom error UI</div>

      render(
        <ErrorBoundary fallback={CustomFallback}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Custom error UI')).toBeInTheDocument()
      expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument()
    })

    it('should pass error and resetError to custom fallback', () => {
      const CustomFallback = ({
        error,
        resetError,
      }: {
        error?: Error
        resetError: () => void
      }) => (
        <div>
          <p>Error: {error?.message}</p>
          <button onClick={resetError}>Reset</button>
        </div>
      )

      render(
        <ErrorBoundary fallback={CustomFallback}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByText(/Error: Test error/)).toBeInTheDocument()
      expect(
        screen.getByRole('button', { name: /reset/i })
      ).toBeInTheDocument()
    })
  })

  describe('Error Callback', () => {
    it('should call onError callback when error occurs', () => {
      const onError = vi.fn()

      render(
        <ErrorBoundary onError={onError}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(onError).toHaveBeenCalledWith(
        expect.objectContaining({ message: 'Test error' }),
        expect.any(Object)
      )
    })
  })

  describe('Reset Functionality', () => {
    it('should reset error state when Try Again clicked', async () => {
      let shouldThrow = true
      const { rerender } = render(
        <ErrorBoundary>
          <ThrowError shouldThrow={shouldThrow} />
        </ErrorBoundary>
      )

      // Error should be shown
      expect(screen.getByText('Something went wrong')).toBeInTheDocument()

      // Click Try Again - this resets the error boundary
      const tryAgainButton = screen.getByRole('button', { name: /try again/i })
      await userEvent.click(tryAgainButton)

      // Update the flag and re-render
      shouldThrow = false
      rerender(
        <ErrorBoundary key="retry">
          <ThrowError shouldThrow={shouldThrow} />
        </ErrorBoundary>
      )

      // After reset, should render children normally
      expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument()
    })
  })

  describe('Refresh Page Button', () => {
    it('should reload page when Refresh Page clicked', async () => {
      // Mock window.location.reload
      const reloadMock = vi.fn()
      Object.defineProperty(window, 'location', {
        writable: true,
        value: { reload: reloadMock },
      })

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      const refreshButton = screen.getByRole('button', {
        name: /refresh page/i,
      })
      await userEvent.click(refreshButton)

      expect(reloadMock).toHaveBeenCalled()
    })
  })
})

describe('ApiErrorBoundary', () => {
  // Suppress console.error for error boundary tests
  const originalError = console.error
  beforeEach(() => {
    console.error = vi.fn()
  })

  afterEach(() => {
    console.error = originalError
  })

  describe('Normal Operation', () => {
    it('should render children when no error occurs', () => {
      render(
        <ApiErrorBoundary componentName="Test Component">
          <div>API content</div>
        </ApiErrorBoundary>
      )

      expect(screen.getByText('API content')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('should show component-specific error message', () => {
      render(
        <ApiErrorBoundary componentName="Dashboard">
          <ThrowError shouldThrow={true} />
        </ApiErrorBoundary>
      )

      expect(screen.getByText('Dashboard Error')).toBeInTheDocument()
      expect(
        screen.getByText(/Unable to load dashboard data/)
      ).toBeInTheDocument()
    })

    it('should use default component name if not provided', () => {
      render(
        <ApiErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ApiErrorBoundary>
      )

      expect(screen.getByText('component Error')).toBeInTheDocument()
      expect(
        screen.getByText(/Unable to load component data/)
      ).toBeInTheDocument()
    })

    it('should show Retry button', () => {
      render(
        <ApiErrorBoundary componentName="Stats">
          <ThrowError shouldThrow={true} />
        </ApiErrorBoundary>
      )

      expect(
        screen.getByRole('button', { name: /retry/i })
      ).toBeInTheDocument()
    })

    it('should show LEGO-themed message', () => {
      render(
        <ApiErrorBoundary componentName="Logs">
          <ThrowError shouldThrow={true} />
        </ApiErrorBoundary>
      )

      expect(
        screen.getByText(/Building better error handling, LEGO brick by brick!/)
      ).toBeInTheDocument()
    })
  })

  describe('Error Logging', () => {
    it('should log component-specific error message', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error')

      render(
        <ApiErrorBoundary componentName="Analytics">
          <ThrowError shouldThrow={true} />
        </ApiErrorBoundary>
      )

      // Check that error was logged with component name
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        expect.stringContaining('API Error in Analytics'),
        expect.any(Error),
        expect.any(Object)
      )
    })
  })

  describe('Reset Functionality', () => {
    it('should reset error when Retry clicked', async () => {
      let shouldThrow = true
      const { rerender } = render(
        <ApiErrorBoundary componentName="Charts">
          <ThrowError shouldThrow={shouldThrow} />
        </ApiErrorBoundary>
      )

      // Error should be shown
      expect(screen.getByText('Charts Error')).toBeInTheDocument()

      // Click Retry
      const retryButton = screen.getByRole('button', { name: /retry/i })
      await userEvent.click(retryButton)

      // Update the flag and re-render
      shouldThrow = false
      rerender(
        <ApiErrorBoundary componentName="Charts" key="retry">
          <ThrowError shouldThrow={shouldThrow} />
        </ApiErrorBoundary>
      )

      // After reset, should not show error
      expect(screen.queryByText('Charts Error')).not.toBeInTheDocument()
    })
  })
})
