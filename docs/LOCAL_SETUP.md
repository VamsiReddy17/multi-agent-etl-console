# Local Setup Guide

## Prerequisites

| Tool | Minimum Version | Install |
|------|----------------|---------|
| Docker | 20.10+ | https://docs.docker.com/get-docker/ |
| Docker Compose | 2.0+ | Bundled with Docker Desktop |
| Python | 3.9+ | https://python.org |

---

## Step 1 — Clone & Navigate

```bash
cd "Agents Dev/production-pipeline"
```

---

## Step 2 — Install Python Dependencies (Local Dev)

```bash
pip install python-dotenv pyyaml psycopg2-binary kafka-python pytest
```

---

## Step 3 — Configure Environment

```bash
cp .env.example .env
# Edit .env if you need to change ports or passwords
```

---

## Step 4 — Start All Docker Services

```bash
docker-compose up -d
```

This starts: **PostgreSQL**, **Zookeeper**, **Kafka**, **Redis**, **Airflow webserver**, **Airflow scheduler**, **Airflow worker**.

Check all containers are healthy:

```bash
docker-compose ps
```

---

## Step 5 — Create Kafka Topics

```bash
chmod +x scripts/create_topics.sh
./scripts/create_topics.sh
```

Topics created: `orders`, `customers`, `products`, `events`, `enriched_orders`

---

## Step 6 — Verify Health

```bash
chmod +x scripts/health_check.sh
./scripts/health_check.sh
```

---

## Step 7 — Run Unit Tests

```bash
cd production-pipeline
pytest tests/ -v
```

---

## Step 8 — Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| Airflow UI | http://localhost:8080 | airflow / airflow |
| PostgreSQL | localhost:5432 | postgres / postgres_password |
| Kafka | localhost:9092 | — |
| Redis | localhost:6379 | — |

---

## Step 9 — Send a Test Kafka Message

```bash
docker exec prod_kafka kafka-console-producer \
  --broker-list localhost:9092 \
  --topic orders

# Then type and press Enter:
{"order_id": 100, "customer_id": 1, "product_id": 1, "quantity": 2, "amount": 99.99, "event_type": "order_placed"}
```

---

## Step 10 — Run the Pipeline Manually

```bash
# From Agents Dev/production-pipeline/
python pipelines/streaming_etl.py --mode once
```

---

## Stopping Services

```bash
docker-compose down          # Stop containers (data preserved)
docker-compose down -v       # Stop + delete all data volumes
```
