import io
import json

from confluent_kafka import Consumer
import avro.schema
import avro.io

# Define Avro schema (same as producer)
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

def deserialize_order(data):
    # Deserialize Avro binary data to order object
    reader = avro.io.DatumReader(order_schema)
    bytes_reader = io.BytesIO(data)
    decoder = avro.io.BinaryDecoder(bytes_reader)
    return reader.read(decoder)

consumer_config = {
    "bootstrap.servers": "localhost:9092",
    "group.id": "order-consumers",
    "auto.offset.reset": "earliest"
}

consumer = Consumer(consumer_config)

consumer.subscribe(["orders"])

print("🟢 Consumer is running and subscribed to orders topic")

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print("❌ Error:", msg.error())
            continue

        order = deserialize_order(msg.value())
        print(f"📦 Received order: {order['order_id']} included {order['product']} at {order['price']}")
except KeyboardInterrupt:
    print("\n🔴 Stopping consumer")

finally:
    consumer.close()