import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { AlertTriangle, RefreshCw } from 'lucide-react'

interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
  errorInfo?: React.ErrorInfo
}

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ComponentType<{ error?: Error; resetError: () => void }>
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void
}

export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error boundary caught an error:', error, errorInfo)

    this.setState({
      error,
      errorInfo,
    })

    // Call the optional error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo)
    }
  }

  resetError = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined })
  }

  render() {
    if (this.state.hasError) {
      // Use custom fallback component if provided
      if (this.props.fallback) {
        const FallbackComponent = this.props.fallback
        return (
          <FallbackComponent
            error={this.state.error}
            resetError={this.resetError}
          />
        )
      }

      // Default error UI
      return (
        <DefaultErrorFallback
          error={this.state.error}
          resetError={this.resetError}
        />
      )
    }

    return this.props.children
  }
}

interface DefaultErrorFallbackProps {
  error?: Error
  resetError: () => void
}

function DefaultErrorFallback({
  error,
  resetError,
}: DefaultErrorFallbackProps) {
  return (
    <Card className="border-lego-red">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lego-red">
          <AlertTriangle className="h-5 w-5" />
          Something went wrong
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-muted-foreground">
          We encountered an unexpected error. This might be due to a temporary
          network issue or server problem.
        </p>

        {error && (
          <details className="text-sm">
            <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
              Technical details
            </summary>
            <div className="mt-2 p-2 bg-muted rounded font-mono text-xs break-all">
              {error.message}
            </div>
          </details>
        )}

        <div className="flex gap-2">
          <Button onClick={resetError} variant="outline" size="sm">
            <RefreshCw className="mr-2 h-4 w-4" />
            Try Again
          </Button>
          <Button
            onClick={() => window.location.reload()}
            variant="outline"
            size="sm"
          >
            Refresh Page
          </Button>
        </div>

        <p className="text-xs text-muted-foreground">
          💡 If this problem persists, try refreshing the page or check your
          network connection.
        </p>
      </CardContent>
    </Card>
  )
}

// API-specific error boundary for dashboard components
interface ApiErrorBoundaryProps {
  children: React.ReactNode
  componentName?: string
}

export function ApiErrorBoundary({
  children,
  componentName = 'component',
}: ApiErrorBoundaryProps) {
  const handleError = (error: Error, errorInfo: React.ErrorInfo) => {
    // Log API-specific errors
    console.error(`API Error in ${componentName}:`, error, errorInfo)
  }

  return (
    <ErrorBoundary
      onError={handleError}
      fallback={({ resetError }) => (
        <Card className="border-lego-orange">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lego-orange">
              <AlertTriangle className="h-5 w-5" />
              {componentName} Error
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-muted-foreground">
              Unable to load {componentName.toLowerCase()} data. This might be
              due to backend connectivity issues.
            </p>

            <Button onClick={resetError} variant="outline" size="sm">
              <RefreshCw className="mr-2 h-4 w-4" />
              Retry
            </Button>

            <p className="text-xs text-muted-foreground">
              🧱 Building better error handling, LEGO brick by brick!
            </p>
          </CardContent>
        </Card>
      )}
    >
      {children}
    </ErrorBoundary>
  )
}

export default ErrorBoundary
