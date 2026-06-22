# Library to connect to PostgreSQL
import os
import sys

import psycopg2
# Library for sentence embeddings
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
load_dotenv()

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
    # Connect to database
    # to connect to PostgreSQL
    conn = psycopg2.connect(DATABASE_URL)
    # to execute queries
    cursor = conn.cursor()

    

    # Fetch content posts WITHOUT embeddings
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

    # For the case where there are no new content posts to embed, we skip the whole pipeline
    if not rows:
        print("No new content to embed.")
        cursor.close()
        conn.close()
        sys.exit(2)

    source_ids = []
    sources = []
    texts = []

    # Fill lists with posts IDs and normalized texts from the SQL query result
    for source_id, source, text in rows:
        source_ids.append(source_id)
        sources.append(source)
        texts.append(normalize_text(text))

    # Create embeddings (BATCHED)
    print(f"Embedding {len(texts)} posts...")
    # Turn texts into embeddings
    embeddings = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        show_progress_bar=True
    )

    # Store embeddings
    # Match post IDs with their embeddings and insert into the database

    for source, source_id, text, vector in zip(sources, source_ids, texts, embeddings):
        try:
            cursor.execute("""
                INSERT INTO content_metadata (source, source_id, embedding, model_name)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (source, source_id) DO NOTHING;
            """, (source, source_id, vector.tolist(), MODEL_NAME))
        except Exception as e:
            print(f"Error inserting embedding for {source} {source_id}: {e}")
            conn.rollback()  # Rollback in case of error to avoid partial commits

    # Save changes
    conn.commit()
    # Clean up
    cursor.close()
    # Close connection
    conn.close()

    # For debugging
    print("Embedding completed successfully.")


if __name__ == "__main__":
    main()
