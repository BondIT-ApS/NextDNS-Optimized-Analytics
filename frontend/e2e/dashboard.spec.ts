import { test, expect } from '@playwright/test'

/**
 * 🧱 Dashboard E2E Tests
 *
 * Tests the /dashboard route which shows system health, database stats,
 * and resource usage cards. AUTH_ENABLED=false so no login required.
 */

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard')
    // Wait until the main content is out of the loading state
    await page.waitForLoadState('networkidle')
  })

  test('loads without errors and shows stat cards', async ({ page }) => {
    // The page should not redirect to /login (auth is disabled)
    await expect(page).toHaveURL(/\/dashboard/)

    // At least one card should appear after data loads
    // Cards have a role="article" or contain known text — check for the
    // Database Records heading which is always present on the Dashboard
    await expect(
      page.getByText(/Database Records|Total Queries|Backend Status/i).first()
    ).toBeVisible({ timeout: 15000 })
  })

  test('shows the Refresh button', async ({ page }) => {
    const refresh = page.getByRole('button', { name: /refresh/i })
    await expect(refresh).toBeVisible({ timeout: 10000 })
  })

  test('Refresh button triggers a new data fetch', async ({ page }) => {
    // Wait for initial load
    await expect(
      page.getByText(/Database Records|Total Queries|Backend Status/i).first()
    ).toBeVisible({ timeout: 15000 })

    // Intercept the health API call
    let healthCallCount = 0
    page.on('request', (req) => {
      if (req.url().includes('/health')) healthCallCount++
    })

    const refresh = page.getByRole('button', { name: /refresh/i })
    await refresh.click()

    // Give React Query time to fire the request
    await page.waitForTimeout(1000)
    expect(healthCallCount).toBeGreaterThan(0)
  })

  test('nav links are visible in the sidebar/header', async ({ page }) => {
    // The layout should render navigation to key routes
    await expect(page.getByRole('link', { name: /stats/i }).first()).toBeVisible({
      timeout: 10000,
    })
    await expect(page.getByRole('link', { name: /logs/i }).first()).toBeVisible()
    await expect(page.getByRole('link', { name: /settings/i }).first()).toBeVisible()
  })
})
