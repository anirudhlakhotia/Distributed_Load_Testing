from kafka import KafkaConsumer, KafkaProducer
import json
import uuid
import threading
import time
import statistics

bootstrap_servers = "localhost:9092"
register_topic = "register"
test_config_topic = "test_config"
heartbeat_topic = "heartbeat"
trigger_topic = "trigger"
metrics_topic = "metrics"

consumer = KafkaConsumer(
    register_topic,
    bootstrap_servers=bootstrap_servers,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")) if v else None,
)

producer = KafkaProducer(
    bootstrap_servers=bootstrap_servers,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

driver_latencies = {}

def send_test_config_message():
    test_id = str(uuid.uuid4())
    test_config_message = {
        "test_id": test_id,
        "test_type": "TSUNAMI",
        "test_message_delay": 0.1,
        "message_count_per_driver": 100,
    }
    producer.send(test_config_topic, value=test_config_message)
    print(f"Sent test configuration message: {test_config_message}")
    
    return test_id

def listen_to_heartbeat():
    heartbeat_consumer = KafkaConsumer(
        heartbeat_topic,
        bootstrap_servers=bootstrap_servers,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")) if v else None,
    )

    for heartbeat_message in heartbeat_consumer:
        heartbeat_data = heartbeat_message.value
        node_id = heartbeat_data.get("node_id")
        print(f"Received heartbeat from node {node_id}")

def process_metrics_message(metrics_data):
    node_id = metrics_data.get("node_id")
    test_id = metrics_data.get("test_id")
    report_id = metrics_data.get("report_id")
    latencies = metrics_data.get("latencies")

    driver_latencies[node_id] = latencies

    print(f"Received metrics from node {node_id}, Test ID: {test_id}, Report ID: {report_id}")

def calculate_aggregate_statistics():
    all_latencies = [latency for latencies in driver_latencies.values() for latency in latencies]

    if all_latencies:
        mean_latency = statistics.mean(all_latencies)
        median_latency = statistics.median(all_latencies)
        mode_latency = statistics.mode(all_latencies)
        min_latency = min(all_latencies)
        max_latency = max(all_latencies)

        print("Aggregate Statistics:")
        print(f"Mean Latency: {mean_latency}")
        print(f"Median Latency: {median_latency}")
        print(f"Mode Latency: {mode_latency}")
        print(f"Min Latency: {min_latency}")
        print(f"Max Latency: {max_latency}")

heartbeat_thread = threading.Thread(target=listen_to_heartbeat)
heartbeat_thread.daemon = True
heartbeat_thread.start()

try:
    for message in consumer:
        data = message.value
        node_id = data.get("node_id")
        node_IP = data.get("node_IP")
        message_type = data.get("message_type")

        print(
            f"Received from 'register' topic: Node ID - {node_id}, Node IP - {node_IP}, Message Type - {message_type}"
        )

        time.sleep(5)
        test_id = send_test_config_message()
        time.sleep(2)

        while True:
            metrics_consumer = KafkaConsumer(
                metrics_topic,
                bootstrap_servers=bootstrap_servers,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")) if v else None,
            )

            for metrics_message in metrics_consumer:
                metrics_data = metrics_message.value
                process_metrics_message(metrics_data)

            calculate_aggregate_statistics()
            time.sleep(5)

except KeyboardInterrupt:
    pass

finally:
    consumer.close()
    producer.flush()
    producer.close()
