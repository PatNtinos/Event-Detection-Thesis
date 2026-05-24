import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import { useEffect, useRef } from 'react'

function FlyToEvent({ event }) {
  const map = useMap()

  useEffect(() => {
    if (event) {
      map.flyTo(event.position, 6, { duration: 1 })
    }
  }, [event, map])

  return null
}

function MapView({ events, selectedEvent, setSelectedEvent }) {
  const markersRef = useRef({})

  useEffect(() => {
    if (selectedEvent && markersRef.current[selectedEvent.id]) {
      markersRef.current[selectedEvent.id].openPopup()
    }
  }, [selectedEvent])

  return (
    <MapContainer
      center={[20, 0]}
      zoom={2}
      minZoom={2}
      style={{ height: '100%', width: '100%' }}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        noWrap={true}
      />

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

      <FlyToEvent event={selectedEvent} />
    </MapContainer>
  )
}

export default MapView