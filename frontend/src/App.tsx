import { Routes, Route } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { Dashboard } from '@/pages/Dashboard'
import { Activities } from '@/pages/Activities'
import { ActivityDetail } from '@/pages/ActivityDetail'
import { Analytics } from '@/pages/Analytics'
import { Coach } from '@/pages/Coach'
import { Settings } from '@/pages/Settings'
import { Metrics } from '@/pages/Metrics'

function App() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="activities" element={<Activities />} />
        <Route path="activities/:id" element={<ActivityDetail />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="coach" element={<Coach />} />
        <Route path="settings" element={<Settings />} />
        <Route path="metrics" element={<Metrics />} />
      </Route>
    </Routes>
  )
}

export default App
