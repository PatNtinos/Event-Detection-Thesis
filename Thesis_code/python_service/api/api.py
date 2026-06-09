import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL")

@app.get("/events")
def get_events():

    conn = psycopg2.connect(DATABASE_URL)

    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, description, first_seen, latitude, longitude
        FROM events
        WHERE first_seen >= NOW() - INTERVAL '24 hours'
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    events = []

    for row in rows:
        events.append({
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "first_seen": str(row[3]),
            "position": [row[4], row[5]]
        })

    return events