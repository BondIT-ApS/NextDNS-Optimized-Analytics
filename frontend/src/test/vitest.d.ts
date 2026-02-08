/// <reference types="vitest" />
import type { TestingLibraryMatchers } from '@testing-library/jest-dom/matchers'

declare module 'vitest' {
  interface Assertion<T = unknown>
    extends jest.Matchers<void>, TestingLibraryMatchers<T, void> {}
  interface AsymmetricMatchersContaining
    extends jest.Matchers<void>, TestingLibraryMatchers<unknown, void> {}
}
