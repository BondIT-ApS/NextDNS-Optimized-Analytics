import { expect, afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

// 🧱 LEGO Test Environment Setup
// Every good LEGO instruction manual starts with setup!

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers)

// Clean up after each test - keep our LEGO workspace tidy! 
afterEach(() => {
  cleanup()
})