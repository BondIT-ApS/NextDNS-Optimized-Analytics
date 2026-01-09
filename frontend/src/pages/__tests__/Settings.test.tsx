import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Settings } from '../Settings'

describe('🧱 Settings Page', () => {
  it('should render the page title', () => {
    render(<Settings />)
    
    expect(screen.getByText('Settings')).toBeInTheDocument()
  })

  it('should render the page description', () => {
    render(<Settings />)
    
    expect(screen.getByText('System configuration and preferences')).toBeInTheDocument()
  })

  it('should render configuration panel card', () => {
    render(<Settings />)
    
    expect(screen.getByText('Configuration Panel')).toBeInTheDocument()
    expect(screen.getByText('System settings and user preferences')).toBeInTheDocument()
  })

  it('should show coming soon message', () => {
    render(<Settings />)
    
    expect(screen.getByText(/Configuration settings coming soon/)).toBeInTheDocument()
  })

  it('should display LEGO-themed message', () => {
    render(<Settings />)
    
    const message = screen.getByText(/🧱 Configuration settings coming soon/)
    expect(message).toBeInTheDocument()
  })
})
