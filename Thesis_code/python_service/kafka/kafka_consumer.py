# We need the KafkaConsumer class
from kafka import KafkaConsumer
# To handle the JSON messages
import json
# To connect to PostgreSQL
import psycopg2


# Connect to PostgreSQL
conn = psycopg2.connect(
    # PostgreSQL credentials
    dbname="thesis_db",
    user="thesis_user",
    password="thesis_pass",
    # PostgreSQL host and port
    host="localhost",
    port=5432
)
# Create a cursor object to interact with the database
cursor = conn.cursor()

consumer = KafkaConsumer(
    # Kafka topic
    'tweets',
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
print("Waiting for messages...")

# SQL command to insert tweet data into tweets table
insert_query = """
INSERT INTO tweets (id, text, created_at, lang, source)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (id) DO NOTHING;
"""



# For each message received
for message in consumer:
    tweet = message.value
    # Print the tweet id, just to be sure it's working
    print(f"[{tweet['created_at']}] {tweet['id']}")

    # Insert tweet into PostgreSQL
    # execute this SQL command
    cursor.execute(insert_query,(
        tweet['id'],
        tweet['text'], 
        tweet['created_at'],
        tweet["lang"], 
        tweet["source"]
    ))
    # Save all changes in the transaction
    conn.commit()
