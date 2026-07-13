# We need the KafkaProducer class
from kafka import KafkaProducer
# Add data sources to fetch events
from python_service.Data_APIs.Data_Sources import fetch_all_events
# To handle the JSON messages
import json
# To simulate streaming
import time

# ========================
# CONFIG
# ========================
KAFKA_TOPIC = "events"
KAFKA_BROKER = "localhost:9092"
POLL_INTERVAL = 3600  # seconds


# ========================
# PRODUCER SETUP
# ========================
def create_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )


# ========================
# MAIN LOOP
# ========================
def run_producer():
    producer = create_producer()

    print("🚀 Kafka Producer started...")

    while True:
        try:
            events = fetch_all_events()

            if not events:
                print("⚠️ No events fetched")
            else:
                for event in events:
                    producer.send(KAFKA_TOPIC, event)

                producer.flush()
                print(f"✅ Sent {len(events)} events to Kafka")

        except Exception as e:
            print("❌ Producer error:", e)

        time.sleep(POLL_INTERVAL)


# ========================
# ENTRY POINT
# ========================
if __name__ == "__main__":
    run_producer()