# We need the KafkaConsumer class
import os

from kafka import KafkaConsumer
# To handle the JSON messages
import json
# To connect to PostgreSQL
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")
# Connect to PostgreSQL
conn = psycopg2.connect(DATABASE_URL)
# Create a cursor object to interact with the database
cursor = conn.cursor()

consumer = KafkaConsumer(
    # Kafka topic
    'events',
    # Kafka broker address
    bootstrap_servers='localhost:9092',
    # Consumer group ID, so it has memory
    group_id='tweet_consumer_group',
    # Read from the latest messages, with earliest it reads from the first tests we made
    auto_offset_reset='latest',
    # Automatically commit
    enable_auto_commit=True,
    # Change bytes back to JSON
    value_deserializer=lambda v: json.loads(v.decode('utf-8'))
)

# So we know it runs
print("🚀 Kafka Consumer started...")
print("Waiting for messages...")

# SQL command to insert tweet data into content table
insert_query = """
INSERT INTO content (source_id, text, created_at, lang, source)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (source, source_id) DO NOTHING;
"""



# For each message received
for message in consumer:
    content = message.value
    
    
    # TESTING PURPOSES
    # Print the content id, just to be sure it's working
    #print(f"[{content.get('created_at')}] {content['source_id']}")

    # Insert content into PostgreSQL
    # execute this SQL command
    try:
        cursor.execute(insert_query,(
            content['source_id'],
            content['text'], 
            content.get('created_at'),
            content["lang"], 
            content["source"]
        ))
    except Exception as e:
        print("DB insert error:", e)
        conn.rollback()    
    # Save all changes in the transaction
    conn.commit()
