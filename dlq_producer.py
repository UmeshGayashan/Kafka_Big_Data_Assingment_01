import io
import json
from datetime import datetime
from typing import Dict, Optional

from confluent_kafka import Producer
import avro.schema
import avro.io

# DLQ configuration
DLQ_TOPIC = "orders.DLQ"

# Define DLQ schema with error information
dlq_schema_dict = {
    "type": "record",
    "name": "OrderDLQ",
    "namespace": "com.example.orders",
    "fields": [
        {"name": "order_id", "type": "string"},
        {"name": "product", "type": "string"},
        {"name": "price", "type": "float"},
        {"name": "error_reason", "type": "string"},
        {"name": "error_timestamp", "type": "string"},
        {"name": "retry_count", "type": "int"},
        {"name": "original_topic", "type": "string"}
    ]
}

# Parse schema
dlq_schema = avro.schema.parse(json.dumps(dlq_schema_dict))

def serialize_dlq_message(dlq_data: dict) -> bytes:
    # Serialize DLQ message to Avro binary format
    writer = avro.io.DatumWriter(dlq_schema)
    bytes_writer = io.BytesIO()
    encoder = avro.io.BinaryEncoder(bytes_writer)
    writer.write(dlq_data, encoder)
    return bytes_writer.getvalue()

class DLQProducer:
    # Producer for Dead Letter Queue - handles failed messages
    
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.producer_config = {
            "bootstrap.servers": bootstrap_servers
        }
        self.producer = Producer(self.producer_config)
    
    def send_to_dlq(self, order_id: str, product: str, price: float, 
                    error_reason: str, retry_count: int = 0, 
                    original_topic: str = "orders") -> bool:
        # Send failed message to Dead Letter Queue
        try:
            dlq_data = {
                "order_id": order_id,
                "product": product,
                "price": price,
                "error_reason": error_reason,
                "error_timestamp": datetime.now().isoformat(),
                "retry_count": retry_count,
                "original_topic": original_topic
            }
            
            serialized_value = serialize_dlq_message(dlq_data)
            
            self.producer.produce(
                topic=DLQ_TOPIC,
                value=serialized_value,
                callback=self._dlq_delivery_callback
            )
            
            self.producer.flush(timeout=5)
            return True
        
        except Exception as e:
            print(f"❌ Failed to send message to DLQ: {e}")
            return False
    
    def _dlq_delivery_callback(self, err, msg):
        # Callback for DLQ message delivery
        if err:
            print(f"❌ DLQ Delivery failed: {err}")
        else:
            print(f"📨 Message sent to DLQ topic '{msg.topic()}' at offset {msg.offset()}")
    
    def close(self):
        # Close the producer
        self.producer.flush()
        self.producer = None

# Example usage
if __name__ == "__main__":
    dlq_producer = DLQProducer()
    
    # Example: Send a failed message to DLQ
    success = dlq_producer.send_to_dlq(
        order_id="order-123",
        product="Toffee",
        price=10.00,
        error_reason="Max retries exceeded - Kafka broker unavailable",
        retry_count=3,
        original_topic="orders"
    )
    
    if success:
        print("✅ Failed message successfully sent to DLQ")
    else:
        print("❌ Failed to send message to DLQ")
    
    dlq_producer.close()
