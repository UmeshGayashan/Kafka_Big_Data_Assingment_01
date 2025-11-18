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

Enjoy robust error handling! 🎉
