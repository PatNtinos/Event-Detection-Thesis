# Library to connect to PostgreSQL
import psycopg2
# Library for sentence embeddings
from sentence_transformers import SentenceTransformer

"""
# Import time module to run the embedding process periodically
# Uncommented at final stages
import time

while True:
    main()  # embed all new tweets
    time.sleep(60)  # wait 1 minute
"""
# -------- CONFIG --------
# Database connection parameters to login to PostgreSQL
DB_CONFIG = {
    "dbname": "thesis_db",
    "user": "thesis_user",
    "password": "thesis_pass",
    "host": "localhost",
    "port": 5432
}

# What SBERT model to use
MODEL_NAME = "all-MiniLM-L6-v2"
# Batch size for embedding
BATCH_SIZE = 16  


# Cleaning function for text
def normalize_text(text: str) -> str:
    """Minimal text cleaning"""
    return text.strip().lower()


def main():
    # 1. Connect to database
    # to connect to PostgreSQL
    conn = psycopg2.connect(**DB_CONFIG)
    # to execute queries
    cursor = conn.cursor()

    # 2. Load SBERT model ONCE
    print("Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)
    print("Model loaded.")

    # 3. Fetch tweets WITHOUT embeddings
    cursor.execute("""
        SELECT t.id, t.text
        FROM tweets t
        LEFT JOIN text_embeddings e 
            ON e.source = 'twitter'
            AND e.source_id = t.id
        WHERE e.source_id IS NULL
        LIMIT 50;
    """)

    # retrieve all rows from the executed query
    rows = cursor.fetchall()

    # For debugging
    if not rows:
        print("No new tweets to embed.")
        return

    tweet_ids = []
    texts = []

    # Fill lists with tweet IDs and normalized texts from the SQL query result
    for tweet_id, text in rows:
        tweet_ids.append(tweet_id)
        texts.append(normalize_text(text))

    # 4. Create embeddings (BATCHED)
    print(f"Embedding {len(texts)} tweets...")
    # Turn texts into embeddings
    embeddings = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        show_progress_bar=True
    )

    # 5. Store embeddings
    # Match tweet IDs with their embeddings and insert into the database
    # For TWITTER
    for tweet_id, text, vector in zip(tweet_ids, texts, embeddings):
        cursor.execute("""
            INSERT INTO text_embeddings (source, source_id, text, embedding, model_name)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (source, source_id) DO NOTHING;
        """, ("twitter",tweet_id, text, vector.tolist(), MODEL_NAME))

    # Saave changes
    conn.commit()
    # Clean up
    cursor.close()
    # Close connection
    conn.close()

    # For debugging
    print("Embedding completed successfully.")


if __name__ == "__main__":
    main()
