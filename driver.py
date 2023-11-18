from kafka import KafkaProducer, KafkaConsumer
import json
import socket
import sys
import time
import threading

bootstrap_servers = "localhost:9092"
register_topic = "register"
heartbeat_topic = "heartbeat"
test_config_topic = "test_config"

producer = KafkaProducer(
    bootstrap_servers=bootstrap_servers,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def get_node_ip():
    return socket.gethostbyname(socket.gethostname())

def send_register_message(node_id):
    register_message = {
        "node_id": node_id,
        "node_IP": get_node_ip(),
        "message_type": "DRIVER_NODE_REGISTER"
    }
    producer.send(register_topic, value=register_message)
    print(f"Sent register message: {register_message}")

def send_heartbeat(node_id):
    heartbeat_message = {
        "node_id": node_id,
        "heartbeat": "YES"
    }
    producer.send(heartbeat_topic, value=heartbeat_message)
    print(f"Sent heartbeat for node {node_id}")

def consume_test_config():
    consumer = KafkaConsumer(
        test_config_topic,
        bootstrap_servers=bootstrap_servers,
        value_deserializer=lambda v: json.loads(v.decode('utf-8')) if v else None,
    )

    for message in consumer:
        test_config_data = message.value
        print(f"Received test configuration: {test_config_data}")

def run(node_id):
    consumer_thread = threading.Thread(target=consume_test_config)
    consumer_thread.daemon = True
    consumer_thread.start()

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
    if len(sys.argv) != 2:
        print("Usage: python3 driver.py <node_id>")
        sys.exit(1)

    node_id = sys.argv[1]
    run(node_id)

