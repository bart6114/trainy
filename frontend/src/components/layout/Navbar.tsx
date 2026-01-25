import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { Activity, Calendar, MessageSquare, Settings, BookOpen, TrendingUp } from 'lucide-react'
import { NotificationButton } from '@/components/wellness/NotificationButton'

const navItems = [
  { href: '/', label: 'Dashboard', icon: Calendar },
  { href: '/activities', label: 'Activities', icon: Activity },
  { href: '/analytics', label: 'Analytics', icon: TrendingUp },
  { href: '/planning', label: 'Coach', icon: MessageSquare },
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
        <nav className="flex flex-1 items-center space-x-6 text-sm font-medium">
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
        <div className="ml-auto">
          <NotificationButton />
        </div>
      </div>
    </header>
  )
}
