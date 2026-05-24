import { useState } from 'react'
import './App.css'
import MapView from './components/MapView'


const eventsData = [
  {
    id: 1,
    title: "Athens Event",
    description: "Event in Athens and i add too many characters to make the description longer and test the layout of the popup in the map view",
    date: "2026-05-19",
    position: [37.9838, 23.7275]
  },
  {
    id: 2,
    title: "Paris Event",
    description: "Event in Paris",
    date: "2026-05-18",
    position: [48.8566, 2.3522]
  },
  {
    id: 3,
    title: "Paris Event1",
    description: "Event in Paris",
    date: "2026-05-18",
    position: [48.8566, 2.3522]
  },
  {
    id: 4,
    title: "Paris Event2",
    description: "Event in Paris",
    date: "2026-05-18",
    position: [48.8566, 2.3522]
  },
  {
    id: 5,
    title: "Paris Event3",
    description: "Event in Paris",
    date: "2026-05-18",
    position: [48.8566, 2.3522]
  },
  {
    id: 6,
    title: "New York Event",
    description: "Event in NYC",
    date: "2026-05-17",
    position: [40.7128, -74.0060]
  }
]

function App() {
  const [selectedEvent, setSelectedEvent] = useState(null)

  return (
    <div className="app">
      <div className="sidebar">
        <h2>Atlas Events</h2>

        {eventsData.map((event) => (
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
          events={eventsData}
          selectedEvent={selectedEvent}
          setSelectedEvent={setSelectedEvent}
        />
      </div>
    </div>
  )
}

export default App