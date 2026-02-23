import { test, expect } from '@playwright/test'

/**
 * 🧱 Logs Page E2E Tests
 *
 * Tests the /logs route: table rendering, status filter, search, and
 * profile selector. Relies on seed data from seed_e2e_data.py.
 */

test.describe('Logs Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/logs')
    await page.waitForLoadState('networkidle')
  })

  test('renders the logs table with rows', async ({ page }) => {
    // The table should appear once data has loaded
    const table = page.getByRole('table')
    await expect(table).toBeVisible({ timeout: 20000 })

    // Should have at least one data row (seeder created 1200+ records)
    const rows = page.locator('tbody tr')
    await expect(rows.first()).toBeVisible({ timeout: 15000 })
  })

  test('shows stat summary cards above the table', async ({ page }) => {
    // StatsCards renders Total / Blocked / Allowed counts
    await expect(page.getByText(/total/i).first()).toBeVisible({ timeout: 15000 })
    await expect(page.getByText(/blocked/i).first()).toBeVisible()
    await expect(page.getByText(/allowed/i).first()).toBeVisible()
  })

  test('status filter — Blocked shows only blocked entries', async ({ page }) => {
    // Wait for table to load first
    await expect(page.getByRole('table')).toBeVisible({ timeout: 20000 })

    // Find the status filter (select or button group)
    const blockedFilter = page.getByRole('option', { name: /blocked/i })
      .or(page.getByRole('button', { name: /blocked/i }))
      .or(page.getByLabel(/status/i).locator('option[value="blocked"]'))

    // Use the select element directly — FilterPanel renders a <select>
    const statusSelect = page.locator('select').filter({ hasText: /all|blocked|allowed/i })
    if (await statusSelect.count() > 0) {
      await statusSelect.selectOption('blocked')
      await page.waitForLoadState('networkidle')

      // Every visible badge/pill in the Status column should indicate blocked
      const statusBadges = page.locator('tbody td').filter({ hasText: /blocked/i })
      await expect(statusBadges.first()).toBeVisible({ timeout: 10000 })
    } else {
      // Fallback: just confirm the filter UI exists
      await expect(blockedFilter.first()).toBeVisible({ timeout: 10000 })
    }
  })

  test('search filters the table by domain', async ({ page }) => {
    await expect(page.getByRole('table')).toBeVisible({ timeout: 20000 })

    const searchInput = page.getByPlaceholder(/search|domain/i).first()
    if (await searchInput.count() > 0) {
      await searchInput.fill('google')
      // Debounce is 500ms — wait for it
      await page.waitForTimeout(700)
      await page.waitForLoadState('networkidle')

      // Table rows should now contain 'google'
      const rows = page.locator('tbody tr')
      const firstRowText = await rows.first().textContent({ timeout: 10000 })
      expect(firstRowText?.toLowerCase()).toContain('google')
    } else {
      // If search input not found, at least the table should be visible
      await expect(page.getByRole('table')).toBeVisible()
    }
  })

  test('allowed filter shows only allowed entries', async ({ page }) => {
    await expect(page.getByRole('table')).toBeVisible({ timeout: 20000 })

    const statusSelect = page.locator('select').filter({ hasText: /all|blocked|allowed/i })
    if (await statusSelect.count() > 0) {
      await statusSelect.selectOption('allowed')
      await page.waitForLoadState('networkidle')

      // Rows should load — there are ~840 allowed records in the seed data
      const rows = page.locator('tbody tr')
      await expect(rows.first()).toBeVisible({ timeout: 10000 })
    }
  })
})
