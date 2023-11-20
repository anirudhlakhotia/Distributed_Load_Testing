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

NUM_DRIVERS = 2

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
registered_drivers = set()

driver_status = {}


def check_driver_status():
    global driver_status
    while True:
        if (
            all(status == "complete" for status in driver_status.values())
            and driver_status
        ):
            print("All driver nodes have completed. Stopping test.")
            # Stop other threads and end the test here
            break
        time.sleep(5)


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
        # print(f"Received heartbeat from node {node_id}")


def send_trigger_message(test_id):
    trigger_message = {"test_id": test_id, "trigger": "YES"}
    producer.send(trigger_topic, value=trigger_message)
    print(f"Sent trigger message to initiate the load test: {trigger_message}")


def check_and_send_test_config():
    if len(registered_drivers) == NUM_DRIVERS:
        test_id = send_test_config_message()
        time.sleep(2)
        send_trigger_message(test_id)


def register_driver(node_id):
    registered_drivers.add(node_id)
    print(f"Registered driver: {node_id}")
    check_and_send_test_config()


def process_metrics_message(metrics_data):
    node_id = metrics_data.get("node_id")
    test_id = metrics_data.get("test_id")
    report_id = metrics_data.get("report_id")
    latencies = metrics_data.get("latencies")
    test_status = metrics_data.get("test_status")
    driver_status[node_id] = test_status
    driver_latencies[node_id] = latencies

    print(
        f"Received metrics from node {node_id}, Test ID: {test_id}, Report ID: {report_id}"
    )
    print()


def calculate_aggregate_statistics():
    all_latencies = [
        latency for latencies in driver_latencies.values() for latency in latencies
    ]

    if all_latencies:
        mean_latency = statistics.mean(all_latencies)
        median_latency = statistics.median(all_latencies)
        mode_latency = statistics.mode(all_latencies)
        min_latency = min(all_latencies)
        max_latency = max(all_latencies)

        print("\n\nUpdated Aggregate Statistics\n\n")
        # print(f"Mean Latency: {mean_latency}")
        # print(f"Median Latency: {median_latency}")
        # print(f"Mode Latency: {mode_latency}")
        # print(f"Min Latency: {min_latency}")
        # print(f"Max Latency: {max_latency}")


def calculate_and_print_aggregate_statistics():
    while True:
        calculate_aggregate_statistics()
        time.sleep(0.1)


def listen_to_metrics():
    global driver_latencies
    metrics_consumer = KafkaConsumer(
        metrics_topic,
        bootstrap_servers=bootstrap_servers,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")) if v else None,
    )

    while True:
        for metrics_message in metrics_consumer:
            metrics_data = metrics_message.value
            process_metrics_message(metrics_data)
        time.sleep(5)


def run_orchestrator():
    heartbeat_thread = threading.Thread(target=listen_to_heartbeat)
    metrics_thread = threading.Thread(target=listen_to_metrics)
    aggregate_metrics_thread = threading.Thread(
        target=calculate_and_print_aggregate_statistics
    )
    driver_status_thread = threading.Thread(target=check_driver_status)

    heartbeat_thread.daemon = True
    metrics_thread.daemon = True
    aggregate_metrics_thread.daemon = True
    driver_status_thread.daemon = True

    heartbeat_thread.start()
    metrics_thread.start()
    aggregate_metrics_thread.start()
    driver_status_thread.start()

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
            register_driver(node_id)

    except KeyboardInterrupt:
        pass

    finally:
        consumer.close()
        producer.flush()
        producer.close()


if __name__ == "__main__":
    run_orchestrator()
