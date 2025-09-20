import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { WifiOff, Clock } from 'lucide-react'
import { useState, useEffect } from 'react'

interface SkeletonProps {
  className?: string
}

export function Skeleton({ className = '' }: SkeletonProps) {
  return <div className={`animate-pulse bg-muted rounded ${className}`} />
}

export function DashboardCardSkeleton() {
  return (
    <Card className="animate-pulse">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-4 w-4" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-8 w-20 mb-2" />
        <Skeleton className="h-3 w-32" />
      </CardContent>
    </Card>
  )
}

export function SystemResourceCardSkeleton() {
  return (
    <Card className="animate-pulse">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Skeleton className="h-5 w-5" />
          <Skeleton className="h-5 w-24" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex justify-between">
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-4 w-12" />
          </div>
          <div className="flex justify-between">
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-4 w-16" />
          </div>
          <Skeleton className="w-full h-2 rounded-full" />
        </div>
      </CardContent>
    </Card>
  )
}

export function SystemInfoSkeleton() {
  return (
    <Card className="animate-pulse">
      <CardHeader>
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-4 w-64" />
      </CardHeader>
      <CardContent>
        {/* Backend Stack */}
        <div>
          <Skeleton className="h-6 w-32 mb-4" />
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[...Array(5)].map((_, i) => (
              <div key={i}>
                <Skeleton className="h-3 w-20 mb-2" />
                <Skeleton className="h-4 w-16" />
              </div>
            ))}
          </div>
        </div>

        {/* Frontend Stack */}
        <div className="mt-6">
          <Skeleton className="h-6 w-36 mb-4" />
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <div key={i}>
                <Skeleton className="h-3 w-20 mb-2" />
                <Skeleton className="h-4 w-24" />
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export function LoadingSpinner({
  size = 'medium',
}: {
  size?: 'small' | 'medium' | 'large'
}) {
  const sizeClasses = {
    small: 'h-4 w-4',
    medium: 'h-6 w-6',
    large: 'h-8 w-8',
  }

  return (
    <div
      className={`animate-spin rounded-full border-2 border-muted border-t-lego-blue ${sizeClasses[size]}`}
    />
  )
}

interface LoadingStateProps {
  message?: string
  showSpinner?: boolean
  className?: string
}

export function LoadingState({
  message = 'Loading...',
  showSpinner = true,
  className = '',
}: LoadingStateProps) {
  return (
    <div className={`flex items-center justify-center gap-3 p-6 ${className}`}>
      {showSpinner && <LoadingSpinner />}
      <span className="text-muted-foreground">{message}</span>
    </div>
  )
}

interface ErrorStateProps {
  message?: string
  onRetry?: () => void
  showRetryButton?: boolean
  className?: string
}

export function ErrorState({
  message = 'Something went wrong',
  onRetry,
  showRetryButton = true,
  className = '',
}: ErrorStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center gap-4 p-6 text-center ${className}`}
    >
      <div className="text-lego-red">
        <svg
          className="h-12 w-12"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
          />
        </svg>
      </div>

      <div>
        <h3 className="text-lg font-semibold text-foreground mb-2">Oops!</h3>
        <p className="text-muted-foreground">{message}</p>
      </div>

      {showRetryButton && onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 bg-lego-blue text-white rounded hover:bg-lego-blue/90 transition-colors"
        >
          Try Again
        </button>
      )}
    </div>
  )
}

// Connection status indicators
interface ConnectionIndicatorProps {
  isConnected: boolean
  isLoading?: boolean
  className?: string
}

export function ConnectionIndicator({
  isConnected,
  isLoading = false,
  className = '',
}: ConnectionIndicatorProps) {
  if (isLoading) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <LoadingSpinner size="small" />
        <span className="text-sm text-muted-foreground">Checking...</span>
      </div>
    )
  }

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div
        className={`w-2 h-2 rounded-full ${
          isConnected ? 'bg-lego-green animate-pulse' : 'bg-lego-red'
        }`}
      />
      <span
        className={`text-sm ${
          isConnected ? 'text-lego-green' : 'text-lego-red'
        }`}
      >
        {isConnected ? 'Connected' : 'Disconnected'}
      </span>
    </div>
  )
}

// Retry logic indicator
interface RetryIndicatorProps {
  isRetrying: boolean
  retryCount: number
  maxRetries: number
  nextRetryIn?: number
  className?: string
}

export function RetryIndicator({
  isRetrying,
  retryCount,
  maxRetries,
  nextRetryIn,
  className = '',
}: RetryIndicatorProps) {
  if (!isRetrying && retryCount === 0) return null

  return (
    <div
      className={`flex items-center gap-2 text-sm text-muted-foreground ${className}`}
    >
      {isRetrying && <LoadingSpinner size="small" />}
      <span>
        {isRetrying
          ? `Retrying... (${retryCount}/${maxRetries})`
          : retryCount > 0
            ? `Retried ${retryCount} times`
            : ''}
        {nextRetryIn && nextRetryIn > 0 && (
          <span> - Next retry in {nextRetryIn}s</span>
        )}
      </span>
    </div>
  )
}

// Offline mode indicators
interface OfflineBannerProps {
  isOffline: boolean
  lastUpdated?: number
  className?: string
}

export function OfflineBanner({
  isOffline,
  lastUpdated,
  className = '',
}: OfflineBannerProps) {
  const [currentTime, setCurrentTime] = useState(Date.now())

  // Update current time every second for live age calculation
  useEffect(() => {
    if (!isOffline || !lastUpdated) return

    const interval = setInterval(() => {
      setCurrentTime(Date.now())
    }, 1000)

    return () => clearInterval(interval)
  }, [isOffline, lastUpdated])

  if (!isOffline) return null

  const age = lastUpdated ? currentTime - lastUpdated : 0

  return (
    <div
      className={`flex items-center gap-3 p-3 bg-lego-orange/10 border border-lego-orange/20 rounded-lg ${className}`}
    >
      <WifiOff className="h-5 w-5 text-lego-orange flex-shrink-0" />
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-lego-orange">
            Offline Mode
          </span>
          <div className="h-1 w-1 rounded-full bg-lego-orange animate-pulse" />
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          Showing cached data from{' '}
          {lastUpdated ? formatLiveAge(age) : 'unknown time'}
        </p>
      </div>
    </div>
  )
}

interface DataFreshnessIndicatorProps {
  isFromCache: boolean
  lastUpdated?: number
  isLoading?: boolean
  className?: string
}

export function DataFreshnessIndicator({
  isFromCache,
  lastUpdated,
  isLoading = false,
  className = '',
}: DataFreshnessIndicatorProps) {
  const [currentTime, setCurrentTime] = useState(Date.now())

  // Update current time every second for live age calculation
  useEffect(() => {
    if (isLoading || (!isFromCache && !lastUpdated)) return

    const interval = setInterval(() => {
      setCurrentTime(Date.now())
    }, 1000)

    return () => clearInterval(interval)
  }, [isFromCache, lastUpdated, isLoading])

  if (isLoading || (!isFromCache && !lastUpdated)) return null

  const age = currentTime - (lastUpdated || Date.now())
  const isStale = age > 60000 // 1 minute

  return (
    <div className={`flex items-center gap-2 text-xs ${className}`}>
      <Clock className="h-3 w-3" />
      <span
        className={`${
          isFromCache
            ? 'text-lego-orange'
            : isStale
              ? 'text-lego-yellow'
              : 'text-muted-foreground'
        }`}
      >
        {isFromCache
          ? `Cached ${formatLiveAge(age)}`
          : `Updated ${formatLiveAge(age)}`}
      </span>
    </div>
  )
}

// Helper function to format age from milliseconds
function formatLiveAge(ageInMs: number): string {
  const seconds = Math.floor(ageInMs / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days > 0) {
    return `${days}d ${hours % 24}h ago`
  } else if (hours > 0) {
    return `${hours}h ${minutes % 60}m ago`
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s ago`
  } else {
    return `${Math.max(0, seconds)}s ago`
  }
}
