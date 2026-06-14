# To extract keywords from texts
import os

from keybert import KeyBERT
from sentence_transformers import SentenceTransformer
# To load Bart for the summarization
from transformers import pipeline
# To connect to PostgreSQL
import psycopg2
#  
import spacy

from geopy.geocoders import Nominatim
from collections import Counter

import torch, transformers
from dotenv import load_dotenv
load_dotenv()

# No position events go to Antarctica
DEFAULT_LAT = -69.6354154
DEFAULT_LON = 0.0


# -------- CONFIG --------
# Database connection parameters to login to PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")

# Embedding model for KeyBERT
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# KeyBERT uses embeddings
kw_model = KeyBERT(model=embedding_model)

# BART summarization model 
summarizer = pipeline(
    "summarization",
    model="facebook/bart-large-cnn",
    device=-1  # CPU
)

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Geocoder
geolocator = Nominatim(user_agent="thesis_app")


def fetch_events_without_metadata():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM events
        WHERE title IS NULL
        OR latitude IS NULL
        OR longitude IS NULL;
    """)

    events = [r[0] for r in cursor.fetchall()]
    conn.close()

    return events

def fetch_event_texts(event_id, limit=20):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT text
        FROM content
        WHERE event_id = %s
        ORDER BY created_at DESC
        LIMIT %s;
    """, (event_id, limit))

    texts = [r[0] for r in cursor.fetchall()]
    conn.close()
    return texts


def store_event_metadata(event_id, title, description):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE events
        SET title = %s,
            description = %s,
            last_updated = now()
        WHERE id = %s;
    """, (title, description, event_id))

    conn.commit()
    conn.close()

#Bring the clusters that need a title and description, excluding the noise cluster (-1)




# Bring the texts of posts from each cluster

# Make a title for the cluster by extracting keywords from the combined texts of the cluster's posts. 
# We use KeyBERT to extract keywords and keyphrases, and we take the top 3 as the title. If no keywords are found, we return "Unknown event".
def generate_event_title(texts):
    combined_text = "\n".join(texts)

    combined_text = "\n".join(texts)[:3000]

    try:
        result = summarizer(
            combined_text,
            max_length=25,
            min_length=5,
            do_sample=False
        )[0]["summary_text"]
    except Exception:
        return "Title Unavailable"

    return result


# Generate a description for the cluster by summarizing the combined texts of the cluster's posts. 
# We use BART to summarize the text, and we limit the summary to 40 words. If the combined text is too long, we truncate it to 3000 characters before summarizing.
def generate_event_description(texts):
      
    combined_text = "\n".join(texts)[:3000]

    try:
        summary = summarizer(
            combined_text,
            max_length=62,
            min_length=13,
            do_sample=False
        )[0]["summary_text"]
    except Exception:
        return "Summary unavailable"

    return summary

# Store the generated title and description in the database, linked to the cluster run and cluster label. 
# If a record for this cluster already exists, we update it with the new title and description.



# Get the latest clustering run ID from the database. This assumes that there is at least one run in the database, and that runs are ordered by their creation time. 
# If no runs are found, we raise an error.






def extract_locations(texts):
    locations = []

    for text in texts:
        doc = nlp(text)

        for ent in doc.ents:
            if ent.label_ in ["GPE", "LOC"]:  # cities, countries, locations
                locations.append(ent.text)

    return locations


def get_best_location(locations):
    if not locations:
        return None

    # Most common location
    counter = Counter(locations)
    return counter.most_common(1)[0][0]


def geocode_location(location_name):
    try:
        loc = geolocator.geocode(location_name)
        if loc:
            return loc.latitude, loc.longitude
    except Exception as e:
        print("Geocoding error:", e)

    return None, None


def update_event_location(event_id, lat, lon):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE events
        SET latitude = %s,
            longitude = %s,
            last_updated = now()
        WHERE id = %s;
    """, (lat, lon, event_id))

    conn.commit()
    conn.close()


# Main function to orchestrate the process: get the latest run ID, fetch clusters, generate titles and descriptions, and store them in the database.
def main():

    print("\n🔍 Starting title/description generation...\n")
    print(torch.__version__)
    print(transformers.__version__)
    event_ids = fetch_events_without_metadata()

    if not event_ids:
        print("No events need metadata.")
        return

    print(f"Generating metadata for {len(event_ids)} events")

    for event_id in event_ids:
        texts = fetch_event_texts(event_id)

        if not texts:
            print(f"No texts found for event {event_id} (no texts)")
            continue

        if len(texts) < 5:
            print(f"Skipping event {event_id} (too small)")
            continue
        
        # --------TITLE AND DESCRIPTION--------
        title = generate_event_title(texts)
        description = generate_event_description(texts)

        store_event_metadata(event_id, title, description)

        # --------LOCATION--------
        locations = extract_locations(texts)

        if not locations:
            print(f"No location found for event {event_id}")
            print(f"Sending it to Antarctica!")
            update_event_location(event_id, DEFAULT_LAT, DEFAULT_LON)
            continue

        best_location = get_best_location(locations)

        lat, lon = geocode_location(best_location)

        if lat is None:
            print(f"Geocoding failed for {best_location}")
            continue

        update_event_location(event_id, lat, lon)

        print(f"Event {event_id} → {best_location} ({lat}, {lon})")

        print(f"Event {event_id} processed")



if __name__ == "__main__":
    main()

