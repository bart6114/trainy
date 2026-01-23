import { useEffect, useRef } from 'react'
import { MapContainer, TileLayer, Polyline, useMap } from 'react-leaflet'
import type { LatLngBounds } from 'leaflet'
import L from 'leaflet'
import type { TrackPoint } from '@/types'

interface ActivityRouteMapProps {
  points: TrackPoint[]
  className?: string
}

function FitBounds({ points }: { points: TrackPoint[] }) {
  const map = useMap()
  const hasFitted = useRef(false)

  useEffect(() => {
    if (points.length > 0 && !hasFitted.current) {
      const bounds: LatLngBounds = L.latLngBounds(
        points.map((p) => [p.lat, p.lng] as [number, number])
      )
      map.fitBounds(bounds, { padding: [20, 20] })
      hasFitted.current = true
    }
  }, [map, points])

  return null
}

export function ActivityRouteMap({ points, className = '' }: ActivityRouteMapProps) {
  if (points.length === 0) {
    return (
      <div className={`flex items-center justify-center bg-muted rounded-lg ${className}`}>
        <p className="text-sm text-muted-foreground">No GPS data available</p>
      </div>
    )
  }

  // Calculate center from first point for initial view
  const center: [number, number] = [points[0].lat, points[0].lng]
  const positions: [number, number][] = points.map((p) => [p.lat, p.lng])

  return (
    <MapContainer
      center={center}
      zoom={13}
      className={`rounded-lg ${className}`}
      style={{ height: '100%', width: '100%', minHeight: '200px' }}
      scrollWheelZoom={false}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <Polyline
        positions={positions}
        pathOptions={{
          color: '#3b82f6',
          weight: 3,
          opacity: 0.8,
        }}
      />
      <FitBounds points={points} />
    </MapContainer>
  )
}
