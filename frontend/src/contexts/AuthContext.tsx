import React, { createContext, useContext, useState, useEffect } from 'react'
import { fetchWithAuth } from '../lib/api'

interface AuthContextType {
  isAuthenticated: boolean
  username: string | null
  authEnabled: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  checkAuthStatus: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: React.ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [username, setUsername] = useState<string | null>(null)
  const [authEnabled, setAuthEnabled] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  // Check if authentication is enabled on mount
  useEffect(() => {
    const checkAuthConfig = async () => {
      try {
        const response = await fetch('/api/auth/config')
        if (response.ok) {
          const config = await response.json()
          setAuthEnabled(config.enabled)

          // If auth is enabled, check authentication status
          if (config.enabled) {
            await checkAuthStatus()
          } else {
            // If auth is disabled, mark as authenticated
            setIsAuthenticated(true)
          }
        }
      } catch (error) {
        console.error('Failed to check auth config:', error)
      } finally {
        setIsLoading(false)
      }
    }

    checkAuthConfig()
  }, [])

  const checkAuthStatus = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      if (!token) {
        setIsAuthenticated(false)
        setUsername(null)
        return
      }

      const response = await fetchWithAuth('/api/auth/status')

      if (response.ok) {
        const data = await response.json()
        setIsAuthenticated(data.authenticated)
        setUsername(data.username)
      } else {
        // Token is invalid, clear it
        localStorage.removeItem('auth_token')
        setIsAuthenticated(false)
        setUsername(null)
      }
    } catch (error) {
      console.error('Failed to check auth status:', error)
      setIsAuthenticated(false)
      setUsername(null)
    }
  }

  const login = async (username: string, password: string) => {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Login failed')
      }

      const data = await response.json()
      localStorage.setItem('auth_token', data.access_token)
      setIsAuthenticated(true)
      setUsername(username)
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem('auth_token')
    setIsAuthenticated(false)
    setUsername(null)

    // Call logout endpoint (optional, mainly for logging)
    fetch('/api/auth/logout', {
      method: 'POST',
    }).catch(error => console.error('Logout API call failed:', error))
  }

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        username,
        authEnabled,
        isLoading,
        login,
        logout,
        checkAuthStatus,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
