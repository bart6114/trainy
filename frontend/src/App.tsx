import { Routes, Route } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { Dashboard } from '@/pages/Dashboard'
import { Activities } from '@/pages/Activities'
import { Progress } from '@/pages/Progress'
import { Analytics } from '@/pages/Analytics'
import { Planning } from '@/pages/Planning'
import { Settings } from '@/pages/Settings'
import { Metrics } from '@/pages/Metrics'

function App() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="activities" element={<Activities />} />
        <Route path="progress" element={<Progress />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="planning" element={<Planning />} />
        <Route path="settings" element={<Settings />} />
        <Route path="metrics" element={<Metrics />} />
      </Route>
    </Routes>
  )
}

export default App
