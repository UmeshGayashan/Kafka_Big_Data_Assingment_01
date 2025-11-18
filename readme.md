# Kafka - Big Data Assingment 01

## Prerequisites

- Python > 3.12.4
- .venv
- Pip

## Local Setup

1. Start Kafka and Schema Registry with Docker

```
docker-compose up -d
```

This will start:
- **Kafka** on `localhost:9092`
- **Schema Registry** on `localhost:8081`

2. Create a new virtual environment and activate

```
python -m venv .venv
```
```
.\.venv\Scripts\activate.ps1  
```

3. Install and upgrade pip

```
pip install --upgrade pip
```
```
python.exe -m pip install --upgrade pip
```

4. Install dependencies

```
pip install -r requirements.txt
```

5. Run Consumer

```
python .\consumer.py
```

6. Run Producer

    ###### 🟢 Open another terminal
```
.\.venv\Scripts\activate.ps1  
```

```
python producer.py
```

---

# ✅ **Avro serialization and Avro Deserialization**

## **1. Adding `confluentinc-schema-registry-client` to requirements.txt**

### **Why?**

Because:

* Avro serialization **cannot be done manually** like JSON.
* Kafka Avro messages require communication with the **Schema Registry**.
* The serializer needs this package to **fetch, register, and manage schemas**.

### **Without it:**

Producer and consumer **cannot encode/decode Avro messages** → your system will fail.

---

# 2. **Producer: Integrating Avro Serialization**

## **Why do we define an Avro schema?**

Avro is **schema-based**.
Kafka connects each message to a version of this schema stored in the Schema Registry.

A simple JSON like this:

```json
{
  "order_id": 1,
  "product": "Phone",
  "price": 899.99
}
```

Cannot be sent as Avro unless there is a schema like:

```json
{
  "type": "record",
  "name": "Order",
  "fields": [
    {"name": "order_id", "type": "int"},
    {"name": "product", "type": "string"},
    {"name": "price", "type": "float"}
  ]
}
```

### **Why replace manual JSON encoding?**

JSON:

* Is slow
* Is not strongly typed
* Has no data evolution support
* Requires no schema registry

Avro:

* Strongly typed
* Binary (smaller + faster)
* Supports schema evolution
* Requires Schema Registry

---

# 3. **Consumer: Using AvroDeserializer**

### **Why remove manual JSON decoding?**

Previously for JSON

```python
json.loads(msg.value().decode("utf-8"))
```

BUT for Avro:

* Data is binary
* It includes schema ID
* It must fetch schema from Schema Registry
* JSON decoding **cannot understand Avro binary format**

So:

```python
AvroDeserializer(schema_registry_client, schema_str)
```

Which:

* Automatically checks which schema version was used
* Converts the Avro bytes → Python dict
* Handles all compatibility rules

---

# 4. **Schema Registry Requirement**

### **Why do we need Schema Registry?**

Because Avro messages store **only schema ID**, not the schema itself.

Meaning:

* Producer sends binary Avro + schema ID
* Consumer fetches that schema ID from Schema Registry
* Then properly deserializes the message

### **If Schema Registry is NOT running:**

* Producer cannot register schema
* Consumer cannot decode schema
* Kafka cluster fails immediately

This is why you must add Schema Registry in Docker:

```yaml
schema-registry:
  image: confluentinc/cp-schema-registry
  ports:
    - "8081:8081"
  environment:
    SCHEMA_REGISTRY_KAFKASTORE_BOOTSTRAP_SERVERS: "kafka:9092"
    SCHEMA_REGISTRY_LISTENERS: "http://0.0.0.0:8081"
```

---

# ⭐ **In Summary**

| Update                        | Why It Is Done                                      |
| ----------------------------- | --------------------------------------------------- |
| Add schema-registry-client    | Required to communicate with Schema Registry        |
| Use AvroSerializer            | To convert dict → Avro binary using schema          |
| Use AvroDeserializer          | To convert Avro binary → Python dict using schema   |
| Remove JSON encoding/decoding | JSON is text-based; Avro is binary and schema-based |
| Run Schema Registry           | Required for schema versioning + evolution          |

---


* **Producer retries = 3**
* **Consumer retries = 5**

---

# ✅ **Why Different Retry Counts Are Perfectly Fine**

Producers and consumers face **different types of failures**, so they need **different retry strategies**.

---

# 🔵 **Producer Retry Logic (usually small, like 3)**

Producer retries handle issues such as:

* Temporary network failure
* Kafka broker is overloaded
* Leader election happening

If the producer keeps retrying too much:

* It can cause blocking
* It slows down publishing new messages
* Messages might be duplicated

So producer retries are kept small:

```
2–5 retries (commonly 3)
```

---

# 🟢 **Consumer Retry Logic (can be higher, like 5)**

Consumers fail for different reasons:

* External API call failed
* Database temporarily down
* Data processing error
* Slow downstream system

Consumers usually NEED more retries to recover.

So they commonly use:

```
3–10 retries
```

And if still failing → send to **DLQ**.

---

# 🧠 **Why Consumers Should Retry More**

Because consumers perform more operations:

* Multiple system calls
* Validations
* Data transformations
* Database writes

Producers only *send* data, so they need fewer retries.

---

# 📝 Example Real-World Setup

| Component | Typical Retries   | Reason                               |
| --------- | ----------------- | ------------------------------------ |
| Producer  | 2–3               | Fast fail to avoid blocking pipeline |
| Consumer  | 5–7               | Allow external systems to recover    |
| DLQ       | After max retries | Final safe storage                   |

This setup is **industry standard**.

---

# 🚨 **Dead Letter Queue (DLQ) Implementation**

## **What is a DLQ?**

A **Dead Letter Queue** is a special topic where messages that cannot be processed are sent after exhausting all retry attempts.

**Topic Name:** `orders.DLQ`

### **When Messages Go to DLQ:**

1. ✗ Producer fails after max retries (3 attempts)
2. ✗ Consumer deserialization fails
3. ✗ Aggregation processing error
4. ✗ Unexpected errors during message handling

---

## **DLQ Setup**

### **1. Create DLQ Topic**

```powershell
python .\setup_dlq.py
```

This creates the `orders.DLQ` topic with:
- Partition: 1
- Replication Factor: 1
- Retention: 7 days

### **2. DLQ Message Structure**

DLQ messages contain:
```json
{
  "order_id": "string",           // Original order ID
  "product": "string",             // Product name
  "price": "float",                // Order price
  "error_reason": "string",        // Why it failed
  "error_timestamp": "string",     // When it failed (ISO format)
  "retry_count": "int",            // How many retries attempted
  "original_topic": "string"       // Which topic it came from
}
```

---

## **Running DLQ System**

### **Terminal 1: Start Consumer**
```powershell
.\.venv\Scripts\Activate.ps1
python .\consumer_aggregation.py
```

### **Terminal 2: Send Messages (Producer)**
```powershell
.\.venv\Scripts\Activate.ps1
python producer.py
```

### **Terminal 3: Monitor DLQ (Optional)**
```powershell
.\.venv\Scripts\Activate.ps1
python .\dlq_consumer.py
```

---

## **DLQ Components**

### **dlq_producer.py**
- Sends failed messages to `orders.DLQ`
- Includes error reason and metadata
- Automatically called when retries are exhausted

### **dlq_consumer.py**
- Monitors the DLQ topic
- Tracks error statistics
- Displays failed message summaries
- Useful for debugging and analysis

### **setup_dlq.py**
- Creates the DLQ topic automatically
- Configures retention policies
- Run once before first use

---

## **DLQ Integration**

**Producer** → Sends to DLQ if:
- Max retries exceeded
- Unexpected serialization error

**Consumer Aggregation** → Sends to DLQ if:
- Message deserialization fails
- Processing error occurs

---

## **DLQ Monitoring**

When running `dlq_consumer.py`, you'll see:

```
🚨 DEAD LETTER MESSAGE RECEIVED
   Order ID: abc-123
   Product: Toffee
   Price: $10.00
   Error Reason: Max retries exceeded - Kafka broker unavailable
   Timestamp: 2025-11-17T01:45:30
   Retry Count: 3
   Original Topic: orders
```

**Final Summary** shows:
- Total failed messages
- Errors grouped by reason
- All failed orders listed

---

## **DLQ Workflow Diagram**

```
Producer
   ↓
[Retry 1, 2, 3]
   ↓
Success? → Process normally ✅
   ↓
Failure? → Send to DLQ 🚨
```

---

## **Files Added/Modified**

| File | Purpose |
|------|---------|
| `dlq_producer.py` | Sends failed messages to DLQ |
| `dlq_consumer.py` | Monitors and analyzes DLQ |
| `setup_dlq.py` | Creates DLQ topic |
| `producer.py` | Updated with DLQ integration |
| `consumer_aggregation.py` | Updated with DLQ integration |

---

## **Notes**

- Messages are serialized in **Avro binary format** in DLQ too
- DLQ is **read-only** for analysis
- Failed messages are **never automatically retried** from DLQ
- Use DLQ data for debugging and monitoring production issues

---

# 🚨 Dead Letter Queue (DLQ) Quick Start Guide

## Setup Steps

### 1. Create DLQ Topic
```powershell
python .\setup_dlq.py
```

### 2. Run the System

**Terminal 1 - Aggregation Consumer:**
```powershell
.\.venv\Scripts\Activate.ps1
python .\consumer_aggregation.py
```

**Terminal 2 - Producer (send messages):**
```powershell
.\.venv\Scripts\Activate.ps1
python producer.py
```

**Terminal 3 - DLQ Consumer (optional, monitor failures):**
```powershell
.\.venv\Scripts\Activate.ps1
python .\dlq_consumer.py
```

---

## DLQ System Overview

### **What Happens:**

1. **Producer sends order** → `orders` topic
2. **Consumer processes** → Calculates running average
3. **If processing fails** → Send to `orders.DLQ` topic
4. **DLQ Consumer** → Monitors and reports failures

### **Message Flow:**

```
Producer 
   ↓
Orders Topic 
   ├─→ Success ✅ → Aggregation Consumer
   └─→ Failure ❌ → DLQ Topic (orders.DLQ)
        ↓
        DLQ Consumer (monitoring)
```

---

## DLQ Message Example

When a message fails and goes to DLQ, it contains:

```python
{
    "order_id": "550e8400-e29b-41d4-a716-446655440000",
    "product": "Toffee",
    "price": 10.0,
    "error_reason": "Max retries exceeded - Kafka broker unavailable",
    "error_timestamp": "2025-11-17T14:30:45.123456",
    "retry_count": 3,
    "original_topic": "orders"
}
```

---

## Files Involved

| File | Role |
|------|------|
| `dlq_producer.py` | Sends messages to DLQ |
| `dlq_consumer.py` | Reads & monitors DLQ |
| `setup_dlq.py` | Creates DLQ topic |
| `producer.py` | Produces orders (integrated with DLQ) |
| `consumer_aggregation.py` | Processes orders (integrated with DLQ) |

---

## Testing DLQ

### **Test 1: Simulate Producer Failure**
Stop Kafka and run producer:
```powershell
python producer.py
```
→ Message will go to DLQ after 3 retries

### **Test 2: Monitor DLQ**
Run DLQ consumer to see failed messages:
```powershell
python .\dlq_consumer.py
```
→ Shows all failed messages with error reasons

### **Test 3: Normal Operation**
Run complete system (all 3 terminals) with Kafka running:
- Messages process normally
- DLQ stays empty (unless error occurs)

---

## Key Features

✅ **Automatic Routing** - Failed messages automatically sent to DLQ
✅ **Error Tracking** - Records why each message failed
✅ **Retry Metadata** - Tracks how many retries were attempted
✅ **Timestamp Logging** - Records when failure occurred
✅ **Original Source** - Knows which topic message came from
✅ **Statistics** - DLQ consumer provides summary statistics
✅ **Avro Serialization** - DLQ messages also use Avro binary format

---

## Troubleshooting

### DLQ Consumer won't connect?
→ Make sure Kafka is running: `docker-compose up -d`

### No messages in DLQ?
→ That's good! It means all messages are processing successfully

### Want to see DLQ in action?
→ Stop Kafka, run producer, watch messages go to DLQ

---

## Real-World Scenarios

**Scenario 1: Kafka Broker Down**
- Producer tries 3 times → fails → goes to DLQ
- When Kafka is back, messages stay in DLQ for analysis

**Scenario 2: Bad Data Format**
- Consumer can't deserialize → goes to DLQ
- DLQ consumer shows error: "Deserialization failed"

**Scenario 3: Processing Error**
- Aggregation logic fails → goes to DLQ
- Error reason recorded for debugging

---

## DLQ Retention Policy

- **Duration:** 7 days (configured in `setup_dlq.py`)
- **Purpose:** Analyze failures within a week
- **After 7 days:** Messages are auto-deleted

---

## Next Steps

1. ✅ Run `setup_dlq.py` to create topic
2. ✅ Start `consumer_aggregation.py`
3. ✅ Run `producer.py` to send orders
4. ✅ Optional: Monitor with `dlq_consumer.py`
5. ✅ Check DLQ when errors occur

