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

function FlyToEvent({ event, markersRef }) {
  const map = useMap()

  useEffect(() => {
    if (!event) return

    const marker = markersRef.current[event.id]
    if (!marker) return

    const markerParent = marker.__parent

    if (markerParent) {
      // Clustered — let zoomToShowLayer handle pan + zoom in one motion
      const clusterGroup = markerParent._group
      clusterGroup.zoomToShowLayer(marker, () => {
        setTimeout(() => {
          marker.openPopup()
        }, 100)
      })
    } else {
      // Already standalone — fly directly, never zooming below current zoom
      const targetZoom = Math.max(map.getZoom(), 6)
      map.flyTo(event.position, targetZoom, { duration: 1.3 })
      map.once('moveend', () => {
        marker.openPopup()
      })
    }
  }, [event, map, markersRef])

  return null
}

function MapView({ events, selectedEvent, setSelectedEvent }) {
  const markersRef = useRef({})

  return (
    <MapContainer
      center={[20, 0]}
      zoom={2}
      minZoom={2}
      maxZoom={7}
      maxBounds={[[-85, -180], [85, 180]]}
      maxBoundsViscosity={1.0}
      worldCopyJump={true}
      style={{ height: '100%', width: '100%' }}
    >
      <TileLayer
        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"
        attribution='Tiles &copy; Esri'
        noWrap={false}
      />
      <MarkerClusterGroup
          showCoverageOnHover={false}
          spiderfyOnEveryZoom={false}
          zoomToBoundsOnClick={true}
         // disableClusteringAtZoom={8}
        >
        {events.map((event) => (
          <Marker
            key={event.id}
            position={event.position}
            ref={(ref) => {
              if (ref) {
              markersRef.current[event.id] = ref
            } else {
              delete markersRef.current[event.id]
            }
            }}  
            eventHandlers={{
              click: (e) => {
                e.target.closePopup()
                setSelectedEvent(event)
              }
            }}
          >
            <Popup>
              <h3>{event.title}</h3>
              <p>{event.description}</p>
              <small>                    
                      {new Date(event.first_seen).toLocaleString("en-GB", {
                      day: "2-digit",
                      month: "2-digit",
                      year: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                      hour12: false,
                      timeZone: "UTC"
              })} UTC
              </small>
            </Popup>
          </Marker>
        ))}
      </MarkerClusterGroup>
      <FlyToEvent event={selectedEvent} markersRef={markersRef} />
    </MapContainer>
  )
}

export default MapView