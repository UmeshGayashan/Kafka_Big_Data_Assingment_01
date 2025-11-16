import json
import uuid

from confluent_kafka import Producer

producer_config = {
    "bootstrap.servers": "localhost:9092"
}

producer = Producer(producer_config)

order = {
    "order_id": str(uuid.uuid4()),
    "product": "Toffee",
    "price": 10.00
}

value = json.dumps(order).encode("utf-8")

producer.produce(
    topic="orders",
    value=value
)

producer.flush()