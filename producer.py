import uuid
import io
import json
import time
from typing import Optional

from confluent_kafka import Producer
import avro.schema
import avro.io

# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 2

# Define Avro schema
order_schema_dict = {
    "type": "record",
    "name": "Order",
    "namespace": "com.example.orders",
    "fields": [
        {"name": "order_id", "type": "string"},
        {"name": "product", "type": "string"},
        {"name": "price", "type": "float"}
    ]
}

# Parse schema
order_schema = avro.schema.parse(json.dumps(order_schema_dict))

def serialize_order(order):
    # Serialize order object to Avro binary format
    writer = avro.io.DatumWriter(order_schema)
    bytes_writer = io.BytesIO()
    encoder = avro.io.BinaryEncoder(bytes_writer)
    writer.write(order, encoder)
    return bytes_writer.getvalue()

producer_config = {
    "bootstrap.servers": "localhost:9092",
    "message.send.max.retries": MAX_RETRIES,
    "retry.backoff.ms": RETRY_BACKOFF_SECONDS * 1000
}

producer = Producer(producer_config)

def delivery_report(err, msg):
    if err:
        print(f"❌ Delivery failed: {err}")
    else:
        print(f"✅ Delivered message to {msg.topic()} : partition {msg.partition()} : at offset {msg.offset()}")

def produce_with_retry(producer: Producer, topic: str, order: dict, retries: int = MAX_RETRIES) -> bool:
    # Produce a message with automatic retry logic for temporary failures
    for attempt in range(1, retries + 1):
        try:
            serialized_value = serialize_order(order)
            producer.produce(
                topic=topic,
                value=serialized_value,
                callback=delivery_report
            )
            producer.flush(timeout=5)
            return True
        except BufferError as e:
            if attempt < retries:
                print(f"⚠️  Attempt {attempt}/{retries} failed: {e}")
                print(f"   Retrying in {RETRY_BACKOFF_SECONDS} seconds...")
                time.sleep(RETRY_BACKOFF_SECONDS)
            else:
                print(f"❌ Failed to produce message after {retries} attempts: {e}")
                return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    return False

order = {
    "order_id": str(uuid.uuid4()),
    "product": "Toffee",
    "price": 10.00
}

print(f"📤 Producing order {order['order_id']}...")
if produce_with_retry(producer, "orders", order):
    print("✅ Message produced successfully!")
else:
    print("❌ Failed to produce message!")