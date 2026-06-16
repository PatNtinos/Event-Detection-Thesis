import subprocess
import time


def run_module(module_path):
    print(f"\n🚀 Starting {module_path}\n")
    return subprocess.Popen(["python", "-m", module_path])


def main():

    print("\n🎉 Starting the full pipeline...\n")

    # 1️⃣ Start Kafka consumer (background)
    consumer = run_module("python_service.kafka.kafka_consumer")

    # 2️⃣ Start Kafka producer (data ingestion)
    producer = run_module("python_service.kafka.kafka_producer")

    print("\n⏳ Pipeline offset...\n")
    time.sleep(300)
   
    while True:

        # 3️⃣ Run embeddings (batch job)
        embedding_result = subprocess.run(["python", "-m", "python_service.sentence_embedding.embedding"], capture_output=True)
        time.sleep(60)

        if embedding_result.returncode == 2:
            print("\n⏳ No new content to embed, skipping clustering and title generation.\n")
            time.sleep(3600)
            continue

        # 4️⃣ Run clustering
        subprocess.run(["python", "-m", "python_service.event_clustering.clustering"])
        time.sleep(60)

        # 5️⃣ Run title + description generation
        subprocess.run(["python", "-m", "python_service.event_clustering.cluster_title_description"])

        print("\n🎉 PIPELINE FINISHED")
        print("\n⏳ Sleeping for 1 hour...\n")
        time.sleep(3600)


if __name__ == "__main__":
    main()