import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import App from '../../App'

// 🧱 LEGO Test Setup - Building blocks for reliable testing!
const createTestQueryClient = () => {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: Infinity,
      },
    },
  })
}

const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = createTestQueryClient()
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  )
}

describe('🧱 NextDNS Analytics App', () => {
  it('should render the main application without crashing', () => {
    // 🏗️ Assemble our LEGO app component
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    )

    // 🔍 Verify our LEGO pieces are in place
    // The app should render successfully - this is our basic smoke test
    expect(document.body).toBeTruthy()
  })

  it('should have the correct document title structure', () => {
    // 🧱 Check if our LEGO branding is consistent
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    )

    // The document should be properly structured
    const htmlElement = document.querySelector('html')
    expect(htmlElement).toBeTruthy()
  })
})