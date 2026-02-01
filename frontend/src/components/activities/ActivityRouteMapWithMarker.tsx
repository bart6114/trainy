import { useEffect, useRef } from 'react'
import { MapContainer, TileLayer, Polyline, CircleMarker, useMap } from 'react-leaflet'
import type { LatLngBounds } from 'leaflet'
import L from 'leaflet'
import { useActivityTrack } from '@/hooks/useActivities'
import type { TrackPoint } from '@/types'

interface ActivityRouteMapWithMarkerProps {
  activityId: number
  markerPosition: TrackPoint | null
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

function HoverMarker({ position }: { position: TrackPoint | null }) {
  if (!position) return null

  return (
    <CircleMarker
      center={[position.lat, position.lng]}
      radius={8}
      pathOptions={{
        color: '#ef4444',
        fillColor: '#ef4444',
        fillOpacity: 1,
        weight: 2,
      }}
    />
  )
}

export function ActivityRouteMapWithMarker({
  activityId,
  markerPosition,
  className = '',
}: ActivityRouteMapWithMarkerProps) {
  const { data: trackData, isLoading } = useActivityTrack(activityId)

  if (isLoading) {
    return (
      <div className={`flex items-center justify-center bg-muted rounded-lg ${className}`}>
        <p className="text-sm text-muted-foreground">Loading map...</p>
      </div>
    )
  }

  if (!trackData || !trackData.has_track || trackData.points.length === 0) {
    return (
      <div className={`flex items-center justify-center bg-muted rounded-lg ${className}`}>
        <p className="text-sm text-muted-foreground">No GPS data available</p>
      </div>
    )
  }

  const points = trackData.points
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
      <HoverMarker position={markerPosition} />
      <FitBounds points={points} />
    </MapContainer>
  )
}
