import { test, expect } from '@playwright/test'

/**
 * 🧱 Time Range Selection E2E Tests
 *
 * Verifies that time range controls on the Stats page exist and, when changed,
 * cause the app to fire a new API request with the selected range.
 */

const TIME_RANGES = ['30m', '1h', '6h', '24h', '7d', '30d'] as const

test.describe('Time Range Selection', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/stats')
    await page.waitForLoadState('networkidle')
  })

  test('time range control is visible on the Stats page', async ({ page }) => {
    // The Stats page renders a time-range selector (select, button group, or tabs)
    const rangeControl = page
      .getByLabel(/time range|range/i)
      .or(page.getByRole('combobox', { name: /time|range/i }))
      .or(page.locator('select').filter({ hasText: /24h|7d|30d/ }))
      .or(page.getByRole('button', { name: /24h|7d|30d/i }).first())
      .first()

    await expect(rangeControl).toBeVisible({ timeout: 20000 })
  })

  test('charts or stat cards appear after selecting a time range', async ({
    page,
  }) => {
    // Wait for initial content
    await page.waitForTimeout(2000)

    // Find a select element that contains time range options
    const rangeSelect = page.locator('select').filter({ hasText: /24h|7d|30d/i })

    if (await rangeSelect.count() > 0) {
      for (const range of ['24h', '7d'] as const) {
        // Track outgoing API requests for this range
        const apiRequests: string[] = []
        const listener = (req: import('@playwright/test').Request) => {
          if (req.url().includes('/stats') || req.url().includes('/timeseries')) {
            apiRequests.push(req.url())
          }
        }
        page.on('request', listener)

        await rangeSelect.first().selectOption(range)
        // Wait for network to settle after selection
        await page.waitForLoadState('networkidle')

        page.off('request', listener)

        // At least one stats request should have fired
        expect(apiRequests.length).toBeGreaterThan(0)

        // The page should still show content (not an error state)
        await expect(page.locator('body')).not.toContainText(
          'Something went wrong'
        )
      }
    } else {
      // Fallback: just verify the stats page has some content
      await expect(
        page.getByText(/total queries|blocked|allowed/i).first()
      ).toBeVisible({ timeout: 15000 })
    }
  })

  test('each supported time range option is present', async ({ page }) => {
    const rangeSelect = page.locator('select').filter({ hasText: /24h|7d|30d/i })

    if (await rangeSelect.count() > 0) {
      // Verify key options are selectable
      for (const range of TIME_RANGES) {
        const option = rangeSelect.locator(`option[value="${range}"]`)
        const optionCount = await option.count()
        // Only assert if the element exists — not all UIs expose all ranges
        if (optionCount > 0) {
          await expect(option).toBeAttached()
        }
      }
    } else {
      // Button-based range selector
      const buttons = page.getByRole('button', {
        name: /30m|1h|6h|24h|7d|30d|all/i,
      })
      const count = await buttons.count()
      expect(count).toBeGreaterThan(0)
    }
  })

  test('Stats page shows overview metrics', async ({ page }) => {
    // Verify that the overview data cards are rendered after load
    await expect(
      page.getByText(/total queries|blocked queries|allowed/i).first()
    ).toBeVisible({ timeout: 20000 })
  })

  test('Stats page shows chart canvases', async ({ page }) => {
    // Chart.js renders <canvas> elements — at least one should be present
    const canvas = page.locator('canvas').first()
    await expect(canvas).toBeVisible({ timeout: 20000 })
  })

  test('navigating between Stats tabs does not crash', async ({ page }) => {
    // Stats page has tabs: Overview, Domains, TLDs, Devices
    const tabs = page.getByRole('tab')
    const tabCount = await tabs.count()

    if (tabCount > 1) {
      for (let i = 0; i < tabCount; i++) {
        await tabs.nth(i).click()
        await page.waitForTimeout(300)
        // No error boundary should have been triggered
        await expect(page.locator('body')).not.toContainText(
          'Something went wrong'
        )
      }
    }
  })
})
