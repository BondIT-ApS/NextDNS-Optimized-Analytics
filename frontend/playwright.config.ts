import { defineConfig, devices } from '@playwright/test'

/**
 * 🧱 Playwright E2E Configuration
 *
 * Tests run against a live Docker Compose test stack:
 *   - Frontend: http://localhost:5012
 *   - Backend:  http://localhost:5011
 *   - Database: localhost:5434 (PostgreSQL, pre-seeded)
 *
 * AUTH_ENABLED=false in the test environment, so no login flow is needed.
 *
 * To run locally:
 *   docker-compose -f docker-compose.test.yml up -d
 *   python backend/tests/seed_e2e_data.py
 *   npm run test:e2e
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? [['html', { open: 'never' }], ['github']] : 'html',

  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:5012',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // Output directory for Playwright reports and artifacts
  outputDir: 'playwright-results',
})
