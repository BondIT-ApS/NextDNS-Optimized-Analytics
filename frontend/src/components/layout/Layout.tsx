import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/contexts/AuthContext'
import {
  Menu,
  X,
  BarChart3,
  Database,
  Settings,
  Activity,
  Building2,
  TrendingUp,
  LogOut,
  User,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface LayoutProps {
  children: React.ReactNode
}

export function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { isAuthenticated, username, authEnabled, logout } = useAuth()

  const navigation = [
    {
      name: 'Dashboard',
      href: '/dashboard',
      icon: BarChart3,
      description: 'System overview & analytics',
    },
    {
      name: 'Stats',
      href: '/stats',
      icon: TrendingUp,
      description: 'Detailed analytics & insights',
    },
    {
      name: 'DNS Logs',
      href: '/logs',
      icon: Database,
      description: 'View and analyze DNS queries',
    },
    {
      name: 'Settings',
      href: '/settings',
      icon: Settings,
      description: 'System configuration',
    },
  ]

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-lego-blue/5">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 bg-card border-r border-border transform transition-transform duration-200 ease-in-out md:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex h-full flex-col">
          {/* Header */}
          <div className="flex h-16 items-center justify-between px-6 border-b border-border">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-lego-blue rounded flex items-center justify-center">
                <Building2 className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="font-bold text-foreground">NextDNS</h1>
                <p className="text-xs text-muted-foreground">Analytics</p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Stats card */}
          <div className="px-6 py-4 border-b border-border">
            <div className="p-3 bg-gradient-to-r from-lego-blue/10 to-lego-yellow/10 rounded-lg border border-lego-blue/20">
              <div className="flex items-center gap-2 mb-1">
                <Activity className="h-4 w-4 text-lego-blue" />
                <span className="text-sm font-medium text-foreground">
                  System Status
                </span>
              </div>
              <div className="text-xs text-muted-foreground">
                <span>NextDNS Analytics Dashboard</span>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-4 space-y-2">
            {navigation.map(item => {
              const isActive = location.pathname === item.href
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    'group flex items-center px-3 py-3 text-sm font-medium rounded-lg transition-all duration-200',
                    isActive
                      ? 'bg-lego-blue text-white shadow-lg'
                      : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                  )}
                  onClick={() => setSidebarOpen(false)}
                >
                  <item.icon
                    className={cn(
                      'mr-3 h-5 w-5 transition-colors',
                      isActive
                        ? 'text-white'
                        : 'text-muted-foreground group-hover:text-foreground'
                    )}
                  />
                  <div>
                    <div className="font-medium">{item.name}</div>
                    <div
                      className={cn(
                        'text-xs',
                        isActive ? 'text-white/80' : 'text-muted-foreground'
                      )}
                    >
                      {item.description}
                    </div>
                  </div>
                </Link>
              )
            })}
          </nav>

          {/* Footer */}
          <div className="px-4 py-4 border-t border-border space-y-3">
            {/* User info and logout button */}
            {authEnabled && isAuthenticated && username && (
              <div className="flex items-center justify-between px-3 py-2 bg-accent rounded-lg">
                <div className="flex items-center gap-2">
                  <User className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium text-foreground">
                    {username}
                  </span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleLogout}
                  className="h-8 text-xs"
                >
                  <LogOut className="h-3 w-3 mr-1" />
                  Logout
                </Button>
              </div>
            )}

            <div className="text-center">
              <p className="text-xs text-muted-foreground">
                Built with 🧱 by{' '}
                <a
                  href="https://bondit.dk"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-medium text-lego-blue hover:text-lego-blue/80 transition-colors"
                >
                  BondIT ApS
                </a>
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="md:ml-64">
        {/* Top bar */}
        <div className="flex h-16 items-center justify-between px-6 bg-card/80 backdrop-blur-sm border-b border-border">
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-5 w-5" />
          </Button>

          <div className="flex items-center space-x-4">
            <div className="hidden md:block">
              <h2 className="text-lg font-semibold text-foreground">
                {navigation.find(item => item.href === location.pathname)
                  ?.name || 'Dashboard'}
              </h2>
              <p className="text-sm text-muted-foreground">
                {navigation.find(item => item.href === location.pathname)
                  ?.description || 'Welcome to NextDNS Analytics'}
              </p>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="p-6">{children}</main>
      </div>
    </div>
  )
}
