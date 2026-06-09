# Library to connect to PostgreSQL
import os

import psycopg2
# Library for sentence embeddings
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
load_dotenv()

"""
# Import time module to run the embedding process periodically
# Uncommented at final stages
import time

while True:
    main()  # embed all new posts
    time.sleep(60)  # wait 1 minute
"""
# -------- CONFIG --------
# Database connection parameters to login to PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")

# What SBERT model to use
MODEL_NAME = "all-MiniLM-L6-v2"
# Batch size for embedding
BATCH_SIZE = 16  

#  Load SBERT model ONCE
print("Loading embedding model...")
model = SentenceTransformer(MODEL_NAME)
print("Model loaded.")

# Cleaning function for text
def normalize_text(text: str) -> str:
    """Minimal text cleaning"""
    return text.strip()


def main():

    print("\n🔍 Starting embedding process...\n")
    # 1. Connect to database
    # to connect to PostgreSQL
    conn = psycopg2.connect(DATABASE_URL)
    # to execute queries
    cursor = conn.cursor()

    

    # 3. Fetch content posts WITHOUT embeddings
    cursor.execute("""
        SELECT c.source_id, c.source, c.text
        FROM content c
        LEFT JOIN content_metadata e 
            ON e.source = c.source
            AND e.source_id = c.source_id
        WHERE e.source_id IS NULL;
    """)

    # retrieve all rows from the executed query
    rows = cursor.fetchall()

    # For debugging
    if not rows:
        print("No new content to embed.")
        return

    source_ids = []
    sources = []
    texts = []

    # Fill lists with posts IDs and normalized texts from the SQL query result
    for source_id, source, text in rows:
        source_ids.append(source_id)
        sources.append(source)
        texts.append(normalize_text(text))

    # 4. Create embeddings (BATCHED)
    print(f"Embedding {len(texts)} posts...")
    # Turn texts into embeddings
    embeddings = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        show_progress_bar=True
    )

    # 5. Store embeddings
    # Match post IDs with their embeddings and insert into the database
    # For TWITTER
    for source, source_id, text, vector in zip(sources, source_ids, texts, embeddings):
        cursor.execute("""
            INSERT INTO content_metadata (source, source_id, embedding, model_name)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (source, source_id) DO NOTHING;
        """, (source, source_id, vector.tolist(), MODEL_NAME))

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
