# To extract keywords from texts
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer
# To load Bart for the summarization
from transformers import pipeline
# To connect to PostgreSQL
import psycopg2


# -------- CONFIG --------
# Database connection parameters to login to PostgreSQL
DB_CONFIG = {
    "dbname": "thesis_db",
    "user": "thesis_user",
    "password": "thesis_pass",
    "host": "localhost",
    "port": 5432
}

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



def fetch_clusters_for_run(run_id):
    """Return all distinct cluster labels for a run (excluding noise)."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Exclude outliers labeled as -1
    cursor.execute("""
        SELECT DISTINCT cluster_label
        FROM content_metadata
        WHERE cluster_run_id = %s
          AND cluster_label != -1; 
    """, (run_id,))

    # Cluster labels in a list
    clusters = [r[0] for r in cursor.fetchall()]
    conn.close()

    return clusters




def fetch_cluster_texts(run_id, cluster_label, limit=20):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT text
        FROM content_metadata
        WHERE cluster_run_id = %s
          AND cluster_label = %s
        LIMIT %s;
    """, (run_id, cluster_label, limit))

    texts = [r[0] for r in cursor.fetchall()]
    conn.close()

    return texts


def generate_cluster_title(texts):
    combined_text = " ".join(texts)

    keywords = kw_model.extract_keywords(
        combined_text,
        keyphrase_ngram_range=(1, 3),
        stop_words="english",
        top_n=5
    )

    if not keywords:
        return "Unknown event"

    return ", ".join(k[0] for k in keywords[:3])


def generate_cluster_description(texts):
    combined_text = " ".join(texts)[:3000]

    summary = summarizer(
        combined_text,
        max_length=41,
        min_length=13,
        do_sample=False
    )[0]["summary_text"]

    return summary


def store_cluster_metadata(run_id, cluster_label, title, description):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO cluster_properties (cluster_run_id, cluster_label, title, description)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (cluster_run_id, cluster_label)
        DO UPDATE SET
            title = EXCLUDED.title,
            description = EXCLUDED.description;
    """, (run_id, cluster_label, title, description))

    conn.commit()
    conn.close()



def get_latest_run_id():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM clusters_run
        ORDER BY created_at DESC
        LIMIT 1;
    """)

    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise RuntimeError("No clustering runs found.")

    return row[0]




def main():

    
    run_id = get_latest_run_id()
    print(f"Using clustering run {run_id}")

    cluster_labels = fetch_clusters_for_run(run_id)

    if not cluster_labels:
        print("No clusters found.")
        return

    print(f"Generating metadata for {len(cluster_labels)} clusters")

    for label in cluster_labels:
        texts = fetch_cluster_texts(run_id, label)

        if len(texts) < 3:
            print(f"Skipping cluster {label} (too small)")
            continue

        title = generate_cluster_title(texts)
        description = generate_cluster_description(texts)

        store_cluster_metadata(run_id, label, title, description)

        print(f"Cluster {label} processed")



if __name__ == "__main__":
    main()

