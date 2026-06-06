import { useState, useEffect } from 'react'
import './App.css'
import MapView from './components/MapView'






function App() {
  const [selectedEvent, setSelectedEvent] = useState(null)
  const [events, setEvents] = useState([])

  useEffect(() => {
    fetch("https://atlas-6l2c.onrender.com/events")
      .then(res => res.json())
      .then(data => setEvents(data))
      .catch(err => console.error(err))
  }, [])

  return (
    <div className="app">
      <div className="sidebar">
        <h2>AtlasEvents</h2>

        {events.map((event) => (
          <div
            key={event.id}
            className={`event-item ${selectedEvent?.id === event.id ? "active" : ""}`}
            onClick={() => {
              if (selectedEvent?.id === event.id) {
                setSelectedEvent(null)
              } else {
                setSelectedEvent(event)
              }
            }}
          >
            <h3>{event.title}</h3>
            {selectedEvent?.id === event.id && (
                <>
                  <p>{event.description}</p>

                  <span className="event-date">
                    {new Date(event.date).toLocaleDateString()}
                  </span>
                </>
            )}
          </div>
        ))}
      </div>

      <div className="map">
        <MapView
          events={events}
          selectedEvent={selectedEvent}
          setSelectedEvent={setSelectedEvent}
        />
      </div>
    </div>
  )
}

export default App