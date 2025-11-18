import io
import json
import time
from collections import defaultdict

from confluent_kafka import Consumer
import avro.schema
import avro.io

# DLQ configuration
DLQ_TOPIC = "orders.DLQ"
MAX_RETRIES = 5
RETRY_BACKOFF_SECONDS = 3
CONNECTION_TIMEOUT = 10

# Define DLQ schema
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

def deserialize_dlq_message(data: bytes) -> dict:
    # Deserialize DLQ message from Avro binary format
    reader = avro.io.DatumReader(dlq_schema)
    bytes_reader = io.BytesIO(data)
    decoder = avro.io.BinaryDecoder(bytes_reader)
    return reader.read(decoder)

def create_dlq_consumer_with_retry(retries: int = MAX_RETRIES) -> Consumer:
    # Create a DLQ consumer connection with automatic retry logic
    consumer_config = {
        "bootstrap.servers": "localhost:9092",
        "group.id": "dlq-consumer-group",
        "auto.offset.reset": "earliest",
        "socket.timeout.ms": CONNECTION_TIMEOUT * 1000,
        "connections.max.idle.ms": CONNECTION_TIMEOUT * 1000
    }
    
    for attempt in range(1, retries + 1):
        try:
            print(f"🔗 DLQ Consumer connection attempt {attempt}/{retries}...")
            consumer = Consumer(consumer_config)
            consumer.subscribe([DLQ_TOPIC])
            print("✅ DLQ Consumer connected successfully!")
            return consumer
        except Exception as e:
            if attempt < retries:
                print(f"⚠️  Connection failed: {e}")
                print(f"   Retrying in {RETRY_BACKOFF_SECONDS} seconds...")
                time.sleep(RETRY_BACKOFF_SECONDS)
            else:
                print(f"❌ Failed to connect after {retries} attempts: {e}")
                raise
    
    return None

# Statistics tracking
dlq_stats = defaultdict(int)  # Track errors by reason
failed_orders = []  # Store failed order details

consumer = create_dlq_consumer_with_retry()

print("🔴 DLQ Consumer Started - Monitoring Dead Letter Queue")
print("=" * 80)
print(f"📌 Listening on topic: {DLQ_TOPIC}\n")

error_count = 0
max_consecutive_errors = 3

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        
        if msg.error():
            error_count += 1
            print(f"⚠️  Error [{error_count}/{max_consecutive_errors}]: {msg.error()}")
            
            if error_count >= max_consecutive_errors:
                print(f"❌ Too many consecutive errors ({error_count}). Attempting to reconnect...")
                try:
                    consumer.close()
                    consumer = create_dlq_consumer_with_retry()
                    error_count = 0
                except Exception as e:
                    print(f"❌ Failed to reconnect: {e}")
                    raise
            continue
        
        error_count = 0  # Reset error count on successful message
        
        try:
            dlq_message = deserialize_dlq_message(msg.value())
            
            # Track statistics
            dlq_stats[dlq_message['error_reason']] += 1
            failed_orders.append(dlq_message)
            
            # Display DLQ message
            print(f"\n🚨 DEAD LETTER MESSAGE RECEIVED")
            print(f"   Order ID: {dlq_message['order_id']}")
            print(f"   Product: {dlq_message['product']}")
            print(f"   Price: ${dlq_message['price']:.2f}")
            print(f"   Error Reason: {dlq_message['error_reason']}")
            print(f"   Timestamp: {dlq_message['error_timestamp']}")
            print(f"   Retry Count: {dlq_message['retry_count']}")
            print(f"   Original Topic: {dlq_message['original_topic']}")
            print(f"   " + "-" * 70)
            
        except Exception as e:
            print(f"❌ Failed to deserialize DLQ message: {e}")
            continue

except KeyboardInterrupt:
    print("\n\n🔴 Stopping DLQ consumer")
    print("\n📊 DLQ STATISTICS SUMMARY:")
    print("=" * 80)
    
    print(f"\nTotal Failed Messages: {len(failed_orders)}\n")
    
    if dlq_stats:
        print("Errors by Reason:")
        for reason, count in sorted(dlq_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {reason}: {count}")
    
    print("\n" + "-" * 80)
    print("\nFailed Orders Summary:")
    for order in failed_orders:
        print(f"  • Order {order['order_id']}: {order['product']} (${order['price']:.2f}) - {order['error_reason']}")
    
    print("\n" + "=" * 80)

finally:
    consumer.close()
    print("\n✅ DLQ Consumer closed")
