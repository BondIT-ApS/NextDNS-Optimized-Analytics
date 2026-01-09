import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { Login } from '../Login'

// Mock the AuthContext
vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    login: vi.fn(),
    logout: vi.fn(),
    user: null,
    isLoading: false,
  }),
}))

// Wrapper component with required providers
const LoginWithProviders = () => (
  <BrowserRouter>
    <Login />
  </BrowserRouter>
)

describe('🧱 Login Page', () => {
  it('should render login form', () => {
    render(<LoginWithProviders />)

    expect(
      screen.getByRole('textbox', { name: /username/i })
    ).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
  })

  it('should render page title', () => {
    render(<LoginWithProviders />)

    expect(screen.getByText(/NextDNS Analytics/)).toBeInTheDocument()
  })

  it('should render sign in button', () => {
    render(<LoginWithProviders />)

    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('should render username input field', () => {
    render(<LoginWithProviders />)

    const usernameInput = screen.getByLabelText(/username/i)
    expect(usernameInput).toBeInTheDocument()
    expect(usernameInput).toHaveAttribute('type', 'text')
    expect(usernameInput).toHaveAttribute('placeholder', 'Enter your username')
  })

  it('should render password input field', () => {
    render(<LoginWithProviders />)

    const passwordInput = screen.getByLabelText(/password/i)
    expect(passwordInput).toBeInTheDocument()
    expect(passwordInput).toHaveAttribute('type', 'password')
    expect(passwordInput).toHaveAttribute('placeholder', 'Enter your password')
  })

  it('should render LEGO-themed message', () => {
    render(<LoginWithProviders />)

    expect(
      screen.getByText(/Building secure access, one brick at a time/)
    ).toBeInTheDocument()
  })

  it('should render card description', () => {
    render(<LoginWithProviders />)

    expect(
      screen.getByText(
        /Enter your credentials to access your DNS analytics dashboard/
      )
    ).toBeInTheDocument()
  })

  it('should have required fields', () => {
    render(<LoginWithProviders />)

    const usernameInput = screen.getByLabelText(/username/i)
    const passwordInput = screen.getByLabelText(/password/i)

    expect(usernameInput).toBeRequired()
    expect(passwordInput).toBeRequired()
  })
})
