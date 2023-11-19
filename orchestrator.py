from kafka import KafkaConsumer, KafkaProducer
import json
import uuid
import threading
import time

bootstrap_servers = "localhost:9092"
register_topic = "register"
test_config_topic = "test_config"
heartbeat_topic = "heartbeat"
trigger_topic = "trigger"

consumer = KafkaConsumer(
    register_topic,
    bootstrap_servers=bootstrap_servers,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")) if v else None,
)

producer = KafkaProducer(
    bootstrap_servers=bootstrap_servers,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)


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


def send_trigger_message(test_id):
    trigger_message = {"test_id": test_id, "trigger": "YES"}
    producer.send(trigger_topic, value=trigger_message)
    print(f"Sent trigger message to initiate the load test: {trigger_message}")


try:
    heartbeat_thread = threading.Thread(target=listen_to_heartbeat)
    heartbeat_thread.daemon = True
    heartbeat_thread.start()

    for message in consumer:
        data = message.value
        node_id = data.get("node_id")
        node_IP = data.get("node_IP")
        message_type = data.get("message_type")

        print(
            f"Received from 'register' topic: Node ID - {node_id}, Node IP - {node_IP}, Message Type - {message_type}"
        )

        time.sleep(5)
        test_id=send_test_config_message()
        time.sleep(2)
        send_trigger_message(test_id)


except KeyboardInterrupt:
    pass

finally:
    consumer.close()
    producer.flush()
    producer.close()
