#!/usr/bin/env python3

# Script creates the orders.DLQ topic if it doesn't exist.


from confluent_kafka.admin import AdminClient, NewTopic

def create_dlq_topic(bootstrap_servers: str = "localhost:9092", 
                     topic_name: str = "orders.DLQ",
                     num_partitions: int = 1,
                     replication_factor: int = 1) -> bool:
    # Create DLQ topic in Kafka
    
    admin_client = AdminClient({"bootstrap.servers": bootstrap_servers})
    
    # Check if topic exists
    metadata = admin_client.list_topics(timeout=5)
    
    if topic_name in metadata.topics:
        print(f"✅ Topic '{topic_name}' already exists")
        return True
    
    # Create topic
    new_topics = [
        NewTopic(
            topic=topic_name,
            num_partitions=num_partitions,
            replication_factor=replication_factor,
            config={
                "retention.ms": "604800000"  # 7 days retention
            }
        )
    ]
    
    try:
        fs = admin_client.create_topics(new_topics, validate_only=False)
        
        for topic, future in fs.items():
            try:
                future.result()  # The result itself is None
                print(f"✅ Topic '{topic}' created successfully!")
                return True
            except Exception as e:
                print(f"❌ Failed to create topic '{topic}': {e}")
                return False
    
    except Exception as e:
        print(f"❌ Error creating topic: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Kafka DLQ Topic Setup")
    print("=" * 50)
    
    if create_dlq_topic():
        print("\n✅ DLQ setup completed successfully!")
    else:
        print("\n❌ DLQ setup failed!")
