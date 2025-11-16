import uuid
import io
import json

from confluent_kafka import Producer
import avro.schema
import avro.io

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
    "bootstrap.servers": "localhost:9092"
}

producer = Producer(producer_config)

def delivery_report(err, msg):
    if err:
        print(f"❌ Delivery failed: {err}")
    else:
        print(f"✅ Delivered message to {msg.topic()} : partition {msg.partition()} : at offset {msg.offset()}")

order = {
    "order_id": str(uuid.uuid4()),
    "product": "Toffee",
    "price": 10.00
}

producer.produce(
    topic="orders",
    value=serialize_order(order),
    callback=delivery_report
)

producer.flush()