from kafka import KafkaConsumer, KafkaProducer
import json
import socket
import sys
import time
import threading
import random
import os

bootstrap_servers = "localhost:9092"
register_topic = "register"
heartbeat_topic = "heartbeat"
test_config_topic = "test_config"
trigger_topic = "trigger"

producer = KafkaProducer(
    bootstrap_servers=bootstrap_servers,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

ID_FILE_PATH = "driver_node_id.txt"

def generate_unique_id():
    prefix = "DRIVER_"
    timestamp = int(time.time())
    random_component = random.randint(1, 1000000)
    unique_id = f"{prefix}{timestamp}_{random_component}"
    save_id_to_file(unique_id)
    return unique_id

def save_id_to_file(unique_id):
    with open(ID_FILE_PATH, "w") as file:
        file.write(unique_id)

def get_stored_id():
    try:
        with open(ID_FILE_PATH, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return None
        
def delete_id_file():
    try:
        os.remove(ID_FILE_PATH)
    except FileNotFoundError:
        pass

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
        print(f"Received test configuration: {test_config_data}")


def listen_to_trigger():
    consumer = KafkaConsumer(
        trigger_topic,
        bootstrap_servers=bootstrap_servers,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")) if v else None,
    )

    for message in consumer:
        trigger_data = message.value
        print(f"Received trigger: {trigger_data}")


def run():
    stored_id = get_stored_id()

    if stored_id:
        node_id = stored_id
    else:
        new_id = generate_unique_id()
        node_id = new_id

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
    
    delete_id_file()


if __name__ == "__main__":
    #if len(sys.argv) != 2:
    #    print("Usage: python3 driver.py <NODE ID>")
    #    sys.exit(1)

    #node_id = sys.argv[1]
    #run(node_id)
    run()
