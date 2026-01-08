# To connect to PostgreSQL
import psycopg2
# For HDBSCAN clustering
import hdbscan
# For array manipulations
import numpy as np

# -------- CONFIG --------
# Database connection parameters to login to PostgreSQL
DB_CONFIG = {
    "dbname": "thesis_db",
    "user": "thesis_user",
    "password": "thesis_pass",
    "host": "localhost",
    "port": 5432
}

def fetch_embeddings():
    """Fetch embeddings from the database."""
    # Connect with the DB
    conn = psycopg2.connect(**DB_CONFIG)
    # Create a cursor to execute queries
    cursor = conn.cursor()
    
    # Bring the embeddings with their IDs
    cursor.execute("""
        SELECT id, embedding
        FROM content_metadata
        WHERE embedding IS NOT NULL;
    """)
    
    # Get all rows as a list of tuples
    rows = cursor.fetchall()
    # Close the connection
    conn.close()
    
    # If no embeddings found return empty arrays
    if not rows:
        return [], []
    
    # Gets all IDs into a list
    ids = [r[0] for r in rows]
    # Convert embeddings from list to numpy arrays
    embeddings = [np.array(r[1]) for r in rows]
    
    # Return IDs and array of embeddings
    return ids, np.vstack(embeddings) 

def store_clusters_run(min_cluster_size, min_samples):
    """Insert a new clustering run and return its run_id."""
    conn = psycopg2.connect(**DB_CONFIG)
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

def save_cluster_assignments(run_id, ids, labels):
    """Update text_embeddings with cluster info."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # For each embedding ID, update its cluster_id and cluster_label
    for idx, label in zip(ids, labels):
        cursor.execute("""
            UPDATE content_metadata
            SET cluster_id = %s, cluster_label = %s
            WHERE id = %s;
        """, (run_id, int(label), idx))
    
    conn.commit()
    conn.close()

def main():
    # 1. Fetch embeddings
    ids, embeddings = fetch_embeddings()
    if not embeddings.any():
        print("No embeddings found.")
        return
    
    # 2. Run HDBSCAN

    # Minimum number of points to form a cluster
    min_cluster_size = 5
    # Minimum samples in a neighborhood for a point to be a core point
    min_samples = 1
    print(f"Running HDBSCAN with min_cluster_size={min_cluster_size}, min_samples={min_samples}")
    
    clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size,
                                min_samples=min_samples,
                                metric='euclidean')
    
    # Runs the algorithm and gets cluster labels
    labels = clusterer.fit_predict(embeddings)
    
    # 3. Store run info
    run_id = store_clusters_run(min_cluster_size, min_samples)
    
    # 4. Save cluster assignments
    save_cluster_assignments(run_id, ids, labels)
    print(f"Clustering done! {len(set(labels))} clusters found.")

if __name__ == "__main__":
    main()