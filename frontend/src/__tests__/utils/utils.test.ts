// file: frontend/src/__tests__/utils/utils.test.ts
/**
 * 🧱 Unit Tests for Utility Functions
 *
 * Testing our LEGO helper tools - ensuring each utility works perfectly!
 */

import { describe, it, expect } from 'vitest'
import {
  cn,
  formatDate,
  formatBytes,
  formatNumber,
  truncate,
} from '@/lib/utils'

describe('cn (className utility)', () => {
  it('should merge class names correctly', () => {
    const result = cn('foo', 'bar')
    expect(result).toContain('foo')
    expect(result).toContain('bar')
  })

  it('should handle conditional classes', () => {
    const condition = false
    const result = cn('foo', condition && 'bar', 'baz')
    expect(result).toContain('foo')
    expect(result).not.toContain('bar')
    expect(result).toContain('baz')
  })

  it('should handle empty input', () => {
    const result = cn()
    expect(result).toBe('')
  })
})

describe('formatDate', () => {
  it('should format a date string', () => {
    const date = '2024-01-15T10:30:00Z'
    const formatted = formatDate(date)
    expect(formatted).toMatch(/Jan/)
    expect(formatted).toMatch(/15/)
    expect(formatted).toMatch(/2024/)
  })

  it('should format a Date object', () => {
    const date = new Date('2024-01-15T10:30:00Z')
    const formatted = formatDate(date)
    expect(formatted).toMatch(/Jan/)
    expect(formatted).toMatch(/15/)
    expect(formatted).toMatch(/2024/)
  })

  it('should include time in the format', () => {
    const date = '2024-01-15T10:30:00Z'
    const formatted = formatDate(date)
    expect(formatted).toMatch(/\d{1,2}:\d{2}/)
  })
})

describe('formatBytes', () => {
  it('should format zero bytes', () => {
    expect(formatBytes(0)).toBe('0 Bytes')
  })

  it('should format bytes correctly', () => {
    expect(formatBytes(100)).toBe('100 Bytes')
  })

  it('should format kilobytes correctly', () => {
    expect(formatBytes(1024)).toBe('1 KB')
  })

  it('should format megabytes correctly', () => {
    expect(formatBytes(1024 * 1024)).toBe('1 MB')
  })

  it('should format gigabytes correctly', () => {
    expect(formatBytes(1024 * 1024 * 1024)).toBe('1 GB')
  })

  it('should format with decimal precision', () => {
    const result = formatBytes(1536) // 1.5 KB
    expect(result).toBe('1.5 KB')
  })

  it('should handle large numbers', () => {
    const result = formatBytes(1024 * 1024 * 1024 * 1024) // 1 TB
    expect(result).toBe('1 TB')
  })
})

describe('formatNumber', () => {
  it('should format small numbers', () => {
    expect(formatNumber(100)).toBe('100')
  })

  it('should format thousands with commas', () => {
    expect(formatNumber(1000)).toBe('1,000')
  })

  it('should format millions with commas', () => {
    expect(formatNumber(1000000)).toBe('1,000,000')
  })

  it('should handle zero', () => {
    expect(formatNumber(0)).toBe('0')
  })

  it('should handle negative numbers', () => {
    expect(formatNumber(-1000)).toBe('-1,000')
  })
})

describe('truncate', () => {
  it('should not truncate short strings', () => {
    const text = 'Hello'
    expect(truncate(text, 10)).toBe('Hello')
  })

  it('should truncate long strings', () => {
    const text = 'This is a very long string that needs to be truncated'
    const result = truncate(text, 20)
    expect(result).toBe('This is a very long ...')
    expect(result.length).toBe(23) // 20 chars + "..."
  })

  it('should truncate at exact length', () => {
    const text = 'Exactly 10'
    expect(truncate(text, 10)).toBe('Exactly 10')
  })

  it('should handle empty strings', () => {
    expect(truncate('', 10)).toBe('')
  })

  it('should handle edge case of length 0', () => {
    const text = 'Hello'
    expect(truncate(text, 0)).toBe('...')
  })
})
