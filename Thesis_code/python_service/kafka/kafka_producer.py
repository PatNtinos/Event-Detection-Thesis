# We need the KafkaProducer class
from kafka import KafkaProducer
# Add twitter client to fetch tweets
from python_service.twitter_api.twitter_client import fetch_from_twitter_api
# To handle the JSON messages
import json
# To simulate streaming
import time

producer = KafkaProducer(
    # Kafka broker address
    bootstrap_servers='localhost:9092',
    # Change JSON to bytes
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Simulate continuous streaming
while True:
    # Exception if twitter API doesn't work 
    try:
        tweets = fetch_from_twitter_api()
        # Send each tweet to Kafka topic
        for tweet in tweets:
            producer.send('tweets', tweet)
        # Ensure all messages are sent
        producer.flush()
        print(f"Sent {len(tweets)} tweets to Kafka")
    except Exception as e:
        print("Error fetching/sending tweets:", e)
    # Batches of 1 minute MUST CHANGE LATER
    time.sleep(60)
