from kafka import KafkaConsumer, KafkaProducer
import json
import socket
import sys
import time
import threading
import random
import requests
import statistics

bootstrap_servers = "localhost:9092"
register_topic = "register"
heartbeat_topic = "heartbeat"
test_config_topic = "test_config"
trigger_topic = "trigger"
metrics_topic= "metrics"

producer = KafkaProducer(
    bootstrap_servers=bootstrap_servers,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

test_configs = {}


SERVER_IP = "localhost"
SERVER_PORT = 5003

PING_ENDPOINT = f"http://{SERVER_IP}:{SERVER_PORT}/ping"

exit_event = threading.Event()


def send_request_to_server():
    try:
        start_time = time.perf_counter()
        response = requests.get(PING_ENDPOINT)
        end_time = time.perf_counter()
        latency = (end_time - start_time) * 1000
        if response.status_code == 200:
            pass
        else:
            print(f"Request failed. Status Code: {response.status_code}")
        return latency

    except requests.RequestException as e:
        print(f"Request Exception: {e}")
        return None
    


def generate_unique_id():
    prefix = "DRIVER_"
    timestamp = int(time.time())
    random_component = random.randint(1, 1000000)
    unique_id = f"{prefix}{timestamp}_{random_component}"
    return unique_id


def get_node_ip():
    return socket.gethostbyname(socket.gethostname())


def send_register_message(node_id):
    register_message = {
        "node_id": node_id,
        "node_IP": get_node_ip(),
        "message_type": "DRIVER_NODE_REGISTER",
    }
    producer.send(register_topic, value=register_message)
    print(f"Sent register message: {register_message}")


def send_heartbeat(node_id):
    heartbeat_message = {"node_id": node_id, "heartbeat": "YES"}
    producer.send(heartbeat_topic, value=heartbeat_message)
    print(f"Sent heartbeat for node {node_id}")


def consume_test_config():
    consumer = KafkaConsumer(
        test_config_topic,
        bootstrap_servers=bootstrap_servers,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")) if v else None,
    )

    for message in consumer:
        test_config_data = message.value
        test_id = test_config_data["test_id"]

        test_configs[test_id] = test_config_data
        print(f"Received test configuration: {test_config_data}")


def publish_metrics(node_id, test_id, report_id, metrics, test_status, latencies):
    metrics_message = {
        "node_id": node_id,
        "test_id": test_id,
        "report_id": report_id,
        "test_status": test_status,
        "latencies": latencies,
        "metrics": metrics,
    }
    producer.send(metrics_topic, value=metrics_message)
    print(f"Published metrics: {metrics_message}")


def publish_metrics_async(latencies, node_id, test_id, report_id, test_status):
    def worker():
        metrics = calculate_aggregate_metrics(latencies)
        publish_metrics(node_id, test_id, report_id, metrics, test_status, latencies)

    # Create a thread for the non-blocking publish_metrics
    thread = threading.Thread(target=worker)

    # Start the thread
    thread.start()


def calculate_aggregate_metrics(latencies):
    if latencies:
        mean_latency = statistics.mean(latencies)
        median_latency = statistics.median(latencies)
        mode_latency = statistics.mode(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)

        return {
            "mean_latency": mean_latency,
            "median_latency": median_latency,
            "mode_latency": mode_latency,
            "min_latency": min_latency,
            "max_latency": max_latency,
            "num_requests": len(latencies)
        }
    else:
        # Return default metrics if no latencies are available
        return {
            "mean_latency": None,
            "median_latency": None,
            "mode_latency": None,
            "min_latency": None,
            "max_latency": None,
            "num_requests": 0
        }


def avalanche_testing(test_id, message_count_per_driver, node_id):
    latencies = []
    last_time = time.perf_counter()
    report_id = 1

    for _ in range(message_count_per_driver):
        curr_time = time.perf_counter()
        
        if curr_time - last_time > 0.2:
            last_time = curr_time
            publish_metrics_async(latencies, node_id, test_id, report_id, "running")
            report_id += 1

        latency = send_request_to_server()
        if latency:
            latencies.append(latency)
    publish_metrics_async(latencies, node_id, test_id, report_id, "complete")
    time.sleep(1)


def tsunami_testing(test_id, message_count_per_driver, delay_interval, node_id):
    latencies = []
    last_time = time.perf_counter()
    report_id = 1

    for _ in range(message_count_per_driver):
        
        latency = send_request_to_server()
        if latency:
            latencies.append(latency)
            
        curr_time = time.perf_counter()
        
        if curr_time - last_time > 0.2:
            last_time = curr_time
            publish_metrics_async(latencies, node_id, test_id, report_id, "running")
            report_id += 1
        
        time.sleep(delay_interval)
    publish_metrics_async(latencies, node_id, test_id, report_id, "complete")
    time.sleep(1)



def handle_test_config(test_id, node_id):
    test_config = test_configs.get(test_id)

    if test_config:
        test_type = test_config["test_type"]
        message_count_per_driver = test_config["message_count_per_driver"]
        delay_interval = test_config.get("test_message_delay", 0)

        if test_type == "AVALANCHE":
            avalanche_testing(test_id, message_count_per_driver, node_id)
        elif test_type == "TSUNAMI":
            tsunami_testing(test_id, message_count_per_driver, delay_interval, node_id)
        else:
            print(f"Invalid test type: {test_type}")
    else:
        print(f"No test configuration found for test ID: {test_id}")
    
    print("Requests Allocated to this Driver have been completed. Cleaning up and terminating...")
    
    exit_event.set()
    


def listen_to_trigger(node_id):
    consumer = KafkaConsumer(
        trigger_topic,
        bootstrap_servers=bootstrap_servers,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")) if v else None,
    )

    for message in consumer:
        trigger_data = message.value
        print(f"Received trigger: {trigger_data}")

        test_id = trigger_data["test_id"]
        handle_test_config(test_id, node_id)


def run():
    
    node_id = generate_unique_id()

    consumer_thread = threading.Thread(target=consume_test_config)
    trigger_thread = threading.Thread(target=listen_to_trigger, args=(node_id,))

    consumer_thread.daemon = True
    trigger_thread.daemon = True

    consumer_thread.start()
    trigger_thread.start()

    try:
        send_register_message(node_id)
        while not exit_event.is_set():
            send_heartbeat(node_id)
            time.sleep(1)

    except KeyboardInterrupt:
        pass
    finally:
        producer.flush()
        producer.close()


if __name__ == "__main__":
    
    run()
