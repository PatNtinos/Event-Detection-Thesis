import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = "postgresql://neondb_owner:npg_Hi3ntkgCz1jv@ep-solitary-cloud-alrh240q-pooler.c-3.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require" #os.getenv("DATABASE_URL")

@app.get("/events")
def get_events():

    conn = psycopg2.connect(DATABASE_URL)

    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, description, first_seen, latitude, longitude
        FROM events
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