import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { Activity, Calendar, BarChart3, Target, Settings, BookOpen } from 'lucide-react'

const navItems = [
  { href: '/', label: 'Dashboard', icon: Calendar },
  { href: '/activities', label: 'Activities', icon: Activity },
  { href: '/progress', label: 'Progress', icon: BarChart3 },
  { href: '/planning', label: 'Planning', icon: Target },
  { href: '/metrics', label: 'Metrics', icon: BookOpen },
  { href: '/settings', label: 'Settings', icon: Settings },
]

export function Navbar() {
  const location = useLocation()

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        <Link to="/" className="mr-6 flex items-center space-x-2">
          <Activity className="h-6 w-6" />
          <span className="font-bold">Trainy</span>
        </Link>
        <nav className="flex items-center space-x-6 text-sm font-medium">
          {navItems.map((item) => {
            const isActive = location.pathname === item.href
            return (
              <Link
                key={item.href}
                to={item.href}
                className={cn(
                  'flex items-center space-x-1 transition-colors hover:text-foreground/80',
                  isActive ? 'text-foreground' : 'text-foreground/60'
                )}
              >
                <item.icon className="h-4 w-4" />
                <span>{item.label}</span>
              </Link>
            )
          })}
        </nav>
      </div>
    </header>
  )
}
