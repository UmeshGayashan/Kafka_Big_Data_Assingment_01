import io
import json
from collections import defaultdict

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

# Data structure to track running averages per product
product_stats = defaultdict(lambda: {"total_price": 0.0, "count": 0, "running_avg": 0.0})

consumer_config = {
    "bootstrap.servers": "localhost:9092",
    "group.id": "order-aggregation-consumers",
    "auto.offset.reset": "earliest"
}

consumer = Consumer(consumer_config)

consumer.subscribe(["orders"])

print("🟢 Aggregation Consumer is running - Computing running averages per product")
print("=" * 80)

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print("❌ Error:", msg.error())
            continue

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
