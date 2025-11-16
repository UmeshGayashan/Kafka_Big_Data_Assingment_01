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