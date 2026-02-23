import { test, expect } from '@playwright/test'

/**
 * 🧱 Settings Page E2E Tests
 *
 * Verifies the /settings route renders its main sections and key controls.
 * AUTH_ENABLED=false so no login is required.
 */

test.describe('Settings Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings')
    await page.waitForLoadState('networkidle')
  })

  test('loads without errors', async ({ page }) => {
    await expect(page).toHaveURL(/\/settings/)
    // The page title or heading should be visible
    await expect(
      page.getByRole('heading', { name: /settings/i }).first()
    ).toBeVisible({ timeout: 15000 })
  })

  test('shows the NextDNS API key section', async ({ page }) => {
    await expect(
      page.getByText(/api.?key/i, { exact: false }).first()
    ).toBeVisible({ timeout: 15000 })
  })

  test('shows the Profiles section', async ({ page }) => {
    await expect(
      page.getByText(/profile/i, { exact: false }).first()
    ).toBeVisible({ timeout: 15000 })
  })

  test('shows the System Settings section', async ({ page }) => {
    // System settings section covers fetch interval, fetch limit, log level
    await expect(
      page.getByText(/system|fetch interval|fetch limit/i, { exact: false }).first()
    ).toBeVisible({ timeout: 15000 })
  })

  test('Add Profile button is present', async ({ page }) => {
    // There should be a way to add a new profile
    const addButton = page
      .getByRole('button', { name: /add profile|add/i })
      .first()
    await expect(addButton).toBeVisible({ timeout: 15000 })
  })

  test('API key field shows a masked value or configure prompt', async ({ page }) => {
    // The API key section shows a masked key or a prompt to configure
    const apiKeyArea = page
      .getByText(/\*{4,}|not configured|configure/i, { exact: false })
      .or(page.locator('input[type="password"]'))
      .first()

    await expect(apiKeyArea).toBeVisible({ timeout: 15000 })
  })

  test('Save / Update buttons are present for system settings', async ({ page }) => {
    const saveBtn = page
      .getByRole('button', { name: /save|update/i })
      .first()
    await expect(saveBtn).toBeVisible({ timeout: 15000 })
  })
})
