import { Outlet } from 'react-router-dom'
import { Navbar } from './Navbar'

export function AppLayout() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container py-6">
        <Outlet />
      </main>
    </div>
  )
}
