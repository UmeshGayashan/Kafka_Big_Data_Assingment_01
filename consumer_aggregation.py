import io
import json
import time
from collections import defaultdict

from confluent_kafka import Consumer
import avro.schema
import avro.io

# Retry configuration
MAX_RETRIES = 5
RETRY_BACKOFF_SECONDS = 3
CONNECTION_TIMEOUT = 10

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
    """Deserialize Avro binary data to order object"""
    reader = avro.io.DatumReader(order_schema)
    bytes_reader = io.BytesIO(data)
    decoder = avro.io.BinaryDecoder(bytes_reader)
    return reader.read(decoder)

def create_consumer_with_retry(group_id: str, retries: int = MAX_RETRIES) -> Consumer:
    # Create a consumer connection with automatic retry logic
    consumer_config = {
        "bootstrap.servers": "localhost:9092",
        "group.id": group_id,
        "auto.offset.reset": "earliest",
        "socket.timeout.ms": CONNECTION_TIMEOUT * 1000,
        "connections.max.idle.ms": CONNECTION_TIMEOUT * 1000
    }
    
    for attempt in range(1, retries + 1):
        try:
            print(f"🔗 Connection attempt {attempt}/{retries}...")
            consumer = Consumer(consumer_config)
            consumer.subscribe(["orders"])
            print("✅ Consumer connected successfully!")
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

# Data structure to track running averages per product
product_stats = defaultdict(lambda: {"total_price": 0.0, "count": 0, "running_avg": 0.0})

consumer = create_consumer_with_retry("order-aggregation-consumers")

print("🟢 Aggregation Consumer is running - Computing running averages per product")
print("=" * 80)

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
                    consumer = create_consumer_with_retry("order-aggregation-consumers")
                    error_count = 0
                except Exception as e:
                    print(f"❌ Failed to reconnect: {e}")
                    raise
            continue
        
        error_count = 0  # Reset error count on successful message
        
        try:
            order = deserialize_order(msg.value())
            product = order['product']
            price = order['price']
            
            # Update statistics for this product
            product_stats[product]["total_price"] += price
            product_stats[product]["count"] += 1
            product_stats[product]["running_avg"] = product_stats[product]["total_price"] / product_stats[product]["count"]
            
            # Display real-time aggregation
            stats = product_stats[product]
            print(f"\n📊 Order Received: {order['order_id']}")
            print(f"   Product: {product}")
            print(f"   Price: ${price:.2f}")
            print(f"   -------- RUNNING STATISTICS FOR '{product}' --------")
            print(f"   Total Orders: {stats['count']}")
            print(f"   Total Sales: ${stats['total_price']:.2f}")
            print(f"   Running Average Price: ${stats['running_avg']:.2f}")
            print(f"   " + "=" * 50)
        except Exception as e:
            print(f"❌ Failed to process message: {e}")
            continue

except KeyboardInterrupt:
    print("\n\n🔴 Stopping aggregation consumer")
    print("\n📈 FINAL AGGREGATION SUMMARY:")
    print("=" * 80)
    
    for product, stats in sorted(product_stats.items()):
        print(f"\nProduct: {product}")
        print(f"  Total Orders: {stats['count']}")
        print(f"  Total Sales: ${stats['total_price']:.2f}")
        print(f"  Average Price: ${stats['running_avg']:.2f}")
    
    print("\n" + "=" * 80)

finally:
    consumer.close()
