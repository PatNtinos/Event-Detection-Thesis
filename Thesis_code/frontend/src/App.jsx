import { useState, useEffect } from 'react'
import './App.css'
import MapView from './components/MapView'






function App() {
  const [selectedEvent, setSelectedEvent] = useState(null)
  const [events, setEvents] = useState([])

  useEffect(() => {
    fetch("https://atlas-6l2c.onrender.com/events")
      .then(res => res.json())
      .then(data => {
        const sorted = data.sort(
          (a, b) => new Date(b.first_seen) - new Date(a.first_seen)
        )
        setEvents(sorted)
      })
      .catch(err => console.error(err))
  }, [])

  return (
    <div className="app">
      <div className="sidebar">
        <h2>Atlas Events</h2>

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
                    {new Date(event.first_seen).toLocaleString("en-GB", {
                      day: "2-digit",
                      month: "2-digit",
                      year: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                      hour12: false
                    })} UTC
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