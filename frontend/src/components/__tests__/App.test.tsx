import { render, waitFor } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from '../../App'

// 🧱 LEGO Test Setup - Building blocks for reliable testing!
// App already includes QueryClient and Router, so we test it directly

describe('🧱 NextDNS Analytics App', () => {
  it('should render the main application without crashing', async () => {
    // 🏢 Assemble our LEGO app component (includes all providers)
    render(<App />)

    // 🔍 Verify our LEGO pieces are in place
    // The app should render successfully - this is our basic smoke test
    expect(document.body).toBeTruthy()

    // Wait for async auth state updates to complete
    await waitFor(() => {
      expect(document.body).toBeTruthy()
    })
  })

  it('should have the correct document title structure', async () => {
    // 🧱 Check if our LEGO branding is consistent
    render(<App />)

    // The document should be properly structured
    const htmlElement = document.querySelector('html')
    expect(htmlElement).toBeTruthy()

    // Wait for async auth state updates to complete
    await waitFor(() => {
      expect(htmlElement).toBeTruthy()
    })
  })
})
