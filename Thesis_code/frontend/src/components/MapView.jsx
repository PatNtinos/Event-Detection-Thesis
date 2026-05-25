import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import { useEffect, useRef } from 'react'
import MarkerClusterGroup from 'react-leaflet-cluster'
import 'react-leaflet-cluster/dist/assets/MarkerCluster.css'
import 'react-leaflet-cluster/dist/assets/MarkerCluster.Default.css'
import 'leaflet.markercluster'
import L from 'leaflet'

delete L.Icon.Default.prototype._getIconUrl

L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

function FlyToEvent({ event }) {
  const map = useMap()

  useEffect(() => {
    if (event) {
      map.flyTo(event.position, 6, { duration: 1.3 })
    }
  }, [event, map])

  return null
}

function MapView({ events, selectedEvent, setSelectedEvent }) {
  const markersRef = useRef({})

  useEffect(() => {
    const marker = markersRef.current[selectedEvent?.id]
    
    if (marker) {
      setTimeout(() => {
        marker.openPopup()
      }, 50)
    }
  }, [selectedEvent])

  return (
    <MapContainer
      center={[20, 0]}
      zoom={2}
      minZoom={2.3}
      maxBounds={[[-85, -180], [85, 180]]}
      maxBoundsViscosity={1.0}
      worldCopyJump={true}
      style={{ height: '100%', width: '100%' }}
    >
      <TileLayer
        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"
        noWrap={false}
      />
      <MarkerClusterGroup
          showCoverageOnHover={false}
          spiderfyOnEveryZoom={false}
          zoomToBoundsOnClick={true}
        >
        {events.map((event) => (
          <Marker
            key={event.id}
            position={event.position}
            ref={(ref) => {
              markersRef.current[event.id] = ref
            }}
            eventHandlers={{
              click: () => {
                setSelectedEvent(event)
              }
            }}
          >
            <Popup>
              <h3>{event.title}</h3>
              <p>{event.description}</p>
              <small>{new Date(event.date).toLocaleDateString()}</small>
            </Popup>
          </Marker>
        ))}
      </MarkerClusterGroup>
      <FlyToEvent event={selectedEvent} />
    </MapContainer>
  )
}

export default MapView