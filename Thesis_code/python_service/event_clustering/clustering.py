# To connect to PostgreSQL
import os

import psycopg2
# For HDBSCAN clustering
import hdbscan
# For array manipulations
import numpy as np
# To present how many clusters and with how many members
from collections import Counter
from dotenv import load_dotenv
load_dotenv()

# -------- CONFIG --------
# Database connection parameters to login to PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")

def fetch_recent_embeddings():
    """Fetch embeddings from the database."""
    # Connect with the DB
    conn = psycopg2.connect(DATABASE_URL)
    # Create a cursor to execute queries
    cursor = conn.cursor()
    
    # Bring the embeddings with their IDs
    cursor.execute("""
        SELECT id, source, source_id, embedding
        FROM content_metadata
        WHERE embedding IS NOT NULL
        AND created_at >= NOW() - INTERVAL '24 hours';
    """)
    
    # Get all rows as a list of tuples
    rows = cursor.fetchall()
    # Close the connection
    conn.close()
    
    # If no embeddings found return empty arrays
    if not rows:
        return [], [], [], None
    
    ids = []
    sources = []
    source_ids = []
    embeddings = []
    
    for r in rows:
        ids.append(r[0])
        sources.append(r[1])
        source_ids.append(r[2])
        embeddings.append(np.array(r[3]))
    
    # Return IDs and array of embeddings
    return ids, sources, source_ids, np.vstack(embeddings) 

def run_clustering(embeddings):
    clusterer = hdbscan.HDBSCAN(
        # When changing the parameters here, also change them in the main function
        # Parameters for HDBSCAN clustering, bigger numbers = stricter clustering, smaller numbers = more clusters
        min_cluster_size=3,
        min_samples=2,
        metric='euclidean',
    )
    labels = clusterer.fit_predict(embeddings)
    return labels

def load_active_events():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, centroid
        FROM events
        WHERE first_seen >= NOW() - INTERVAL '24 hours';
    """)

    rows = cursor.fetchall()
    conn.close()

    events = []
    for eid, centroid in rows:
        events.append({
            "id": eid,
            "centroid": np.array(centroid)
        })

    return events

def cosine_similarity(a, b):
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0
    return np.dot(a, b) / denom

def match_or_create_events(centroids, events, threshold=0.8):
    cluster_to_event = {}

    for label, centroid in centroids.items():
        best_event = None
        best_score = 0

        for event in events:
            score = cosine_similarity(centroid, event["centroid"])

            if score > best_score:
                best_score = score
                best_event = event

        if best_score >= threshold:
            # The printings are for review purposes
            print(
                f"🔄 Cluster {label} matched Event {best_event['id']} "
                f"(similarity={best_score:.3f})"
            )
            cluster_to_event[label] = best_event["id"]
        else:
            print(
                f"🆕 Cluster {label} is a NEW event "
                f"(best similarity={best_score:.3f})"
            )    
            cluster_to_event[label] = None  # new event

    return cluster_to_event

def update_database(run_id, ids, sources, source_ids, labels, centroids, sizes, cluster_to_event):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()


    for label in centroids.keys():
        event_id = cluster_to_event[label]
        centroid = centroids[label]
        size = sizes[label]

       
        # CREATE NEW EVENT
        if event_id is None:
            print(
                f"🆕 Creating new event from cluster {label}"
                f"({size} articles)"   #Review purposes
            )
            cursor.execute("""
                INSERT INTO events (centroid)
                VALUES (%s)
                RETURNING id;
            """, (centroid.tolist(),))
            event_id = cursor.fetchone()[0]
            print(
                f"🆕 Creating new Event {event_id} "
                f"from cluster {label} "
                f"({size} articles)"
            )
            print(f"✅ Event {event_id} created") #Review purposes
            cluster_to_event[label] = event_id
            

        # UPDATE EXISTING EVENT
        else:
            # Review purposes
            print(
                f"🔄 Updating Event {event_id} "
                f"from cluster {label} "
                f"({size} articles)"
            )
            cursor.execute("""
                UPDATE events
                SET centroid = %s,
                    last_updated = now()
                WHERE id = %s;
            """, (centroid.tolist(), event_id))

        # STORE CLUSTER PROPERTIES
        cursor.execute("""
            INSERT INTO cluster_properties (
                cluster_run_id,
                cluster_label,
                centroid,
                size,
                event_id
            )
            VALUES (%s, %s, %s, %s, %s);
        """, (int(run_id), int(label), centroid.tolist(), int(size), int(event_id)))

    # LINK CONTENT → EVENT
    for i, (meta_id, label) in enumerate(zip(ids, labels)):
        if label == -1:
            continue

        event_id = cluster_to_event[label]

        cursor.execute("""
            UPDATE content
            SET event_id = %s
            WHERE source = %s AND source_id = %s;
        """, (event_id, sources[i], source_ids[i]))

        # ALSO update metadata
        cursor.execute("""
            UPDATE content_metadata
            SET cluster_run_id = %s,
                cluster_label = %s
            WHERE id = %s;
        """, (run_id, int(label), meta_id))

    conn.commit()
    conn.close()


def compute_clusters_info(embeddings, labels):
    clusters = {}

    for i, label in enumerate(labels):
        if label == -1:
            continue  # skip noise
        clusters.setdefault(label, []).append(embeddings[i])

    centroids = {
        int(label): np.mean(vectors, axis=0)
        for label, vectors in clusters.items()
    }

    sizes = {
        int(label): len(vectors)
        for label, vectors in clusters.items()
    }

    return centroids, sizes

def store_clusters_run(min_cluster_size, min_samples):
    """Insert a new clustering run and return its run_id."""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    #Insert the new run with the parameters (defined in main)
    cursor.execute("""
        INSERT INTO clusters_run (min_cluster_size, min_samples)
        VALUES (%s, %s)
        RETURNING id;
    """, (min_cluster_size, min_samples))
    
    run_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    # Retunrn the ID of the new run
    return run_id

def main():

    print("\n🔍 Starting clustering process...\n")

    # Cluster model parameters
    min_cluster_size=3
    min_samples=2
    ids, sources, source_ids, embeddings = fetch_recent_embeddings()

    if embeddings is None or len(embeddings) == 0:
        print("No embeddings found.")
        return

    labels = run_clustering(embeddings)

    centroids, sizes = compute_clusters_info(embeddings, labels)

    # Review Purposes
    print(f"Found {len(centroids)} clusters")
    print(Counter(labels))

    events = load_active_events()

    cluster_to_event = match_or_create_events(centroids, events)

    run_id = store_clusters_run(min_cluster_size, min_samples)

    update_database(
        run_id,
        ids,
        sources,
        source_ids,
        labels,
        centroids,
        sizes,
        cluster_to_event
    )

    print("Clustering + event update completed.")

if __name__ == "__main__":
    main()