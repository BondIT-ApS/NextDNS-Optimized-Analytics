import { expect, afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

// 🧱 LEGO Test Environment Setup
// Every good LEGO instruction manual starts with setup!

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers)

// Mock localStorage that supports Object.keys() iteration
class LocalStorageMock implements Storage {
  private store: Record<string, string> = {}

  getItem(key: string): string | null {
    return this.store[key] || null
  }

  setItem(key: string, value: string): void {
    this.store[key] = value.toString()
  }

  removeItem(key: string): void {
    delete this.store[key]
  }

  clear(): void {
    this.store = {}
  }

  get length(): number {
    return Object.keys(this.store).length
  }

  key(index: number): string | null {
    const keys = Object.keys(this.store)
    return keys[index] || null
  }

  // Make store keys enumerable for Object.keys(localStorage)
  [key: string]: any

  constructor() {
    // Create proxy to make keys enumerable
    return new Proxy(this, {
      ownKeys: target => {
        return Object.keys((target as LocalStorageMock).store)
      },
      getOwnPropertyDescriptor: (target, prop) => {
        if (
          typeof prop === 'string' &&
          (target as LocalStorageMock).store[prop]
        ) {
          return {
            enumerable: true,
            configurable: true,
          }
        }
        return Object.getOwnPropertyDescriptor(target, prop)
      },
    })
  }
}

const localStorageMock = new LocalStorageMock()

// Assign localStorage mock to global
Object.defineProperty(global, 'localStorage', {
  value: localStorageMock,
  writable: true,
})

// Mock fetch for API calls
global.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve({}),
    text: () => Promise.resolve(''),
    headers: new Headers(),
  } as Response)
)

// Clean up after each test - keep our LEGO workspace tidy!
afterEach(() => {
  cleanup()
  localStorage.clear()
  vi.clearAllMocks()
})
