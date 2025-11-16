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