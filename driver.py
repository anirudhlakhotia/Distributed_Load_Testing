from kafka import KafkaConsumer, KafkaProducer
import json
import socket
import sys
import time
import threading
import random
import requests


bootstrap_servers = "localhost:9092"
register_topic = "register"
heartbeat_topic = "heartbeat"
test_config_topic = "test_config"
trigger_topic = "trigger"

producer = KafkaProducer(
    bootstrap_servers=bootstrap_servers,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

test_configs = {}


SERVER_IP = "localhost"
SERVER_PORT = 5003

PING_ENDPOINT = f"http://{SERVER_IP}:{SERVER_PORT}/ping"

def send_request_to_server():
    try:
        response = requests.get(PING_ENDPOINT)
        if response.status_code == 200:
            print("Request successful. Response:", response.json())
        else:
            print(f"Request failed. Status Code: {response.status_code}")

    except requests.RequestException as e:
        print(f"Request Exception: {e}")


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


def avalanche_testing(test_id, message_count_per_driver):
    for _ in range(message_count_per_driver):
        send_request_to_server()


def tsunami_testing(test_id, message_count_per_driver, delay_interval):
    for _ in range(message_count_per_driver):
        send_request_to_server()
        time.sleep(delay_interval)


def handle_test_config(test_id):
    test_config = test_configs.get(test_id)

    if test_config:
        test_type = test_config["test_type"]
        message_count_per_driver = test_config["message_count_per_driver"]
        delay_interval = test_config.get("test_message_delay", 0)

        if test_type == "AVALANCHE":
            avalanche_testing(test_id, message_count_per_driver)
        elif test_type == "TSUNAMI":
            tsunami_testing(test_id, message_count_per_driver, delay_interval)
        else:
            print(f"Invalid test type: {test_type}")
    else:
        print(f"No test configuration found for test ID: {test_id}")


def listen_to_trigger():
    consumer = KafkaConsumer(
        trigger_topic,
        bootstrap_servers=bootstrap_servers,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")) if v else None,
    )

    for message in consumer:
        trigger_data = message.value
        print(f"Received trigger: {trigger_data}")

        test_id = trigger_data["test_id"]
        handle_test_config(test_id)


def run():
    
    node_id = generate_unique_id()

    consumer_thread = threading.Thread(target=consume_test_config)
    trigger_thread = threading.Thread(target=listen_to_trigger)

    consumer_thread.daemon = True
    trigger_thread.daemon = True

    consumer_thread.start()
    trigger_thread.start()

    try:
        send_register_message(node_id)
        while True:
            send_heartbeat(node_id)
            time.sleep(1)

    except KeyboardInterrupt:
        pass
    finally:
        producer.flush()
        producer.close()


if __name__ == "__main__":
    
    run()
