# 🧠 PARENT PROMPT — Production Pipeline Project Context

> **Read this file first.** This is the master context file for the Antigravity IDE.
> Every session should start by reading this file to understand the full project state.

---

## What This Project Is

A **production-ready multi-agent data engineering pipeline** built in Python.
It ingests real-time order events from Apache Kafka, processes them through
4 specialised agents, and loads clean data into a PostgreSQL data warehouse.
Apache Airflow orchestrates and schedules everything.

**Project location**: `/Users/vamsireddy/Desktop/Agents Dev/production-pipeline/`

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Python | 3.9+ |
| Message Broker | Apache Kafka | 7.4.0 (Confluent) |
| Orchestration | Apache Airflow | 2.5.3 |
| Task Queue | Redis + Celery | 7-alpine |
| Database | PostgreSQL | 14-alpine |
| Containerisation | Docker + Compose | 20.10+ |
| Testing | pytest | 7.2.0 |

---

## Project Structure (Complete)

```
production-pipeline/
│
├── agents/                        ← Core agent framework (ALL BUILT ✅)
│   ├── __init__.py
│   ├── config.py                  ← Env-var config (DB, Kafka, logging)
│   ├── kafka_ingestion_agent.py   ← Polls Kafka, decodes JSON
│   ├── transform_agent.py         ← Enriches, coerces types, adds timestamps
│   ├── quality_agent.py           ← Validates, quarantines bad records
│   └── postgres_load_agent.py     ← Batch inserts to PostgreSQL
│
├── pipelines/                     ← Pipeline orchestration (ALL BUILT ✅)
│   ├── streaming_etl.py           ← Main orchestrator: Ingest→Transform→Quality→Load
│   └── config/
│       └── pipeline_config.yaml   ← Batch size, thresholds, schedule config
│
├── airflow/                       ← Airflow config & DAGs (ALL BUILT ✅)
│   ├── airflow.cfg
│   ├── requirements.txt
│   └── dags/
│       ├── __init__.py
│       ├── streaming_etl_dag.py   ← Runs every 5 minutes
│       └── batch_orders_dag.py    ← Runs daily at midnight
│
├── postgres/
│   └── init.sql                   ← DB schema + sample data (5 customers, 5 products, 5 orders)
│
├── kafka/                         ← (empty - managed via Docker)
│
├── monitoring/
│   └── prometheus.yml             ← Prometheus scrape config
│
├── scripts/
│   ├── docker_setup.sh            ← Builds Docker images
│   ├── create_topics.sh           ← Creates Kafka topics
│   └── health_check.sh            ← Checks all services
│
├── tests/                         ← Unit + integration tests (ALL BUILT ✅)
│   ├── __init__.py
│   ├── test_kafka_agent.py
│   ├── test_transform_agent.py
│   ├── test_quality_agent.py
│   ├── test_postgres_agent.py
│   └── test_pipeline.py           ← End-to-end integration test
│
├── architecture/                  ← Architecture docs + diagram (ALL BUILT ✅)
│   ├── README.md
│   ├── architecture_diagram.png
│   ├── ARCHITECTURE.md
│   ├── DATA_FLOW.md
│   ├── AGENT_DESIGN.md
│   └── DECISIONS.md
│
├── docs/                          ← User-facing documentation (ALL BUILT ✅)
│   ├── LOCAL_SETUP.md
│   ├── AIRFLOW_GUIDE.md
│   ├── KAFKA_GUIDE.md
│   └── BIGQUERY_MIGRATION.md
│
├── wip/                           ← 🧠 IDE memory & session tracking (THIS FOLDER)
│   ├── PARENT_PROMPT.md           ← THIS FILE — read first every session
│   ├── SESSION_LOG.md             ← Log of every session's activities
│   ├── COMPLETIONS.md             ← What is 100% done
│   ├── ISSUES.md                  ← Known issues, bugs, blockers
│   └── NEXT_STEPS.md             ← Prioritised backlog
│
├── docker-compose.yml             ← All 7 services defined
├── Dockerfile                     ← Python agent image
├── requirements.txt               ← Python dependencies
└── .env.example                   ← Environment variable template
```

---

## Data Flow (How It Works)

```
External System
      │  JSON event published
      ▼
Apache Kafka :9092  (topic: orders)
      │  KafkaIngestionAgent polls batch
      ▼
Transform Agent  →  type coerce, add timestamps, calc totals
      │
      ▼
Quality Agent    →  validate fields, quarantine bad records
      │                    │
      ▼                    ▼
Load Agent           Quarantined (logged, skipped)
      │
      ▼
PostgreSQL :5432  →  warehouse.order_events
                  →  warehouse.pipeline_execution (audit log)
```

---

## Agent Contracts (Input → Output)

| Agent | Accepts | Returns key fields |
|-------|---------|-------------------|
| KafkaIngestionAgent | `topics: List[str]` | `data: List[Dict], rows: int` |
| TransformAgent | Result from ingestion | `data: List[Dict], rows: int` |
| QualityAgent | Result from transform | `data, rows, quarantined, quarantined_count` |
| PostgresLoadAgent | Result from quality | `rows_loaded: int` |

All agents return: `{status, data, rows, duration_ms, errors, agent}`

---

## Environment Variables

Stored in `.env` (copied from `.env.example`):

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_password
POSTGRES_DB=dataware
KAFKA_BROKER=localhost:9092
KAFKA_TOPIC_ORDERS=orders
KAFKA_GROUP_ID=prod-pipeline-group
KAFKA_BATCH_SIZE=100
LOG_LEVEL=INFO
```

---

## Docker Services

| Container | Image | Port | Role |
|-----------|-------|------|------|
| `prod_postgres` | postgres:14-alpine | 5432 | Data warehouse |
| `prod_zookeeper` | cp-zookeeper:7.4.0 | 2181 | Kafka coordinator |
| `prod_kafka` | cp-kafka:7.4.0 | 9092 | Message broker |
| `prod_redis` | redis:7-alpine | 6379 | Celery task queue |
| `prod_airflow_webserver` | custom | 8080 | Airflow UI |
| `prod_airflow_scheduler` | custom | — | DAG scheduler |
| `prod_airflow_worker` | custom | — | Task executor |

---

## How to Run (Quick Reference)

```bash
# 1. Install local Python deps (for tests only)
pip install python-dotenv pyyaml psycopg2-binary kafka-python pytest

# 2. Run all unit tests (no Docker needed)
cd "/Users/vamsireddy/Desktop/Agents Dev/production-pipeline"
pytest tests/ -v

# 3. Start Docker stack
cp .env.example .env
docker-compose up -d

# 4. Create Kafka topics
./scripts/create_topics.sh

# 5. Add Airflow DB connection
docker exec prod_airflow_webserver airflow connections add postgres_default \
  --conn-type postgres --conn-host postgres --conn-schema dataware \
  --conn-login postgres --conn-password postgres_password --conn-port 5432

# 6. Enable DAGs
docker exec prod_airflow_webserver airflow dags unpause streaming_etl
docker exec prod_airflow_webserver airflow dags unpause batch_orders_etl

# 7. Produce a test message
docker exec prod_kafka kafka-console-producer --broker-list localhost:9092 --topic orders
# Then type: {"order_id": 201, "customer_id": 1, "product_id": 2, "quantity": 2, "amount": 49.99, "event_type": "order_placed"}

# 8. Run pipeline manually
python pipelines/streaming_etl.py --mode once

# 9. Verify data loaded
docker exec prod_postgres psql -U postgres -d dataware \
  -c "SELECT * FROM warehouse.order_events ORDER BY received_at DESC LIMIT 5;"
```

---

## Related Project

There is a sibling reference project:
`/Users/vamsireddy/Desktop/Agents Dev/multi-agent-pipelines/`

This contains the **base agent framework** (pure Python, no infra) with 3 patterns:
- Layered (sequential)
- Type-Based (conditional routing)
- Hierarchical (master-worker)

The production-pipeline builds on these patterns with real infrastructure.

---

## 🚨 NEXT PRIORITY — Data Generator (READ THIS FIRST)

> **Context**: The full pipeline (Kafka → Agents → PostgreSQL) and monitoring
> (Prometheus + Grafana) are all built and running. However, **Kafka is always
> empty** — no real data flows through the pipeline, so Grafana shows all zeros
> and the pipeline always exits with `status: no_data`.
>
> **We need a continuous data generator** that produces realistic fake order
> events into Kafka so that:
> - Data flows through all 4 agents (ingest → transform → quality → load)
> - PostgreSQL `warehouse.order_events` table fills up with real rows
> - Prometheus counters increment with real numbers
> - Grafana dashboards show live, meaningful charts

### What to Build

#### 1. `scripts/generate_orders.py` — Continuous Kafka Producer

A standalone Python script that runs forever (or N times) and publishes
realistic fake orders to the Kafka `orders` topic.

**Requirements:**
- Uses `kafka-python` (`KafkaProducer`) — already in `requirements.txt`
- Produces JSON messages matching the pipeline's expected schema:
  ```json
  {
    "order_id": 401,
    "customer_id": 3,
    "product_id": 2,
    "quantity": 2,
    "amount": 59.98,
    "event_type": "order_placed"
  }
  ```
- Randomises: `order_id` (auto-increment), `customer_id` (1–5),
  `product_id` (1–5), `quantity` (1–10), `amount` (calculated from
  real product prices), `event_type` (order_placed / order_updated /
  order_cancelled)
- Introduces ~10% bad records intentionally (missing fields, negative
  amounts, wrong types) to exercise the Quality Agent's quarantine logic
  and make Grafana's quarantine panel show non-zero values
- Configurable via CLI args:
  - `--rate` : messages per second (default: 1)
  - `--count`: total messages to send (default: 0 = infinite)
  - `--bad-rate`: fraction of bad records (default: 0.1)
  - `--topic`: Kafka topic (default: orders)
- Logs each published message with order_id and timestamp
- Graceful shutdown on Ctrl+C

**File location**: `scripts/generate_orders.py`

#### 2. `scripts/generate_orders.sh` — Convenience Shell Wrapper

A simple shell script that runs the generator inside the Kafka container
(no local Python environment needed):

```bash
#!/bin/bash
# Runs the order generator inside the prod_kafka container
docker exec prod_airflow_webserver python3 /app/scripts/generate_orders.py "$@"
```

**File location**: `scripts/generate_orders.sh`

#### 3. Update `docker-compose.yml` — Optional Generator Service

Add an optional `order_generator` service that auto-starts with the stack:

```yaml
order_generator:
  build:
    context: .
    dockerfile: Dockerfile
  container_name: prod_order_generator
  depends_on:
    - kafka
  environment:
    KAFKA_BROKER: kafka:9092
  command: python3 /app/scripts/generate_orders.py --rate 1 --bad-rate 0.1
  networks:
    - prod_network
  restart: unless-stopped
```

This means `docker-compose up -d` automatically starts generating data
without any manual steps.

### Product Prices (use these for realistic `amount` calculation)

| product_id | name       | price  |
|------------|------------|--------|
| 1          | Laptop     | 999.99 |
| 2          | Mouse      | 29.99  |
| 3          | Keyboard   | 79.99  |
| 4          | Monitor    | 299.99 |
| 5          | Desk Chair | 199.99 |

### Expected End Result After Building This

```
generate_orders.py running (1 msg/sec)
        ↓
   Kafka topic "orders"  ← filling with real events
        ↓
  streaming_etl.py loop  ← picks up batches every 5s
        ↓
  4 agents process data  ← transform, validate, quarantine ~10%
        ↓
  warehouse.order_events ← rows accumulating in PostgreSQL
        ↓
  Prometheus scrapes      ← counters incrementing every 15s
        ↓
  Grafana dashboard       ← live charts showing real throughput
```

### Verification Steps After Building

```bash
# 1. Start the generator (from host)
python3 scripts/generate_orders.py --rate 2 --count 50

# 2. Watch data land in PostgreSQL
docker exec prod_postgres psql -U postgres -d dataware \
  -c "SELECT COUNT(*) FROM warehouse.order_events;"

# 3. Check Prometheus counter is climbing
curl http://localhost:8000/metrics | grep pipeline_runs_total

# 4. Open Grafana at http://localhost:3000
#    → "Streaming ETL Pipeline Dashboard"
#    → Should show non-zero throughput, quarantine rate, latency
```

---

## Current Status

See `wip/COMPLETIONS.md` for what's done.
See `wip/ISSUES.md` for known issues.
See `wip/NEXT_STEPS.md` for what to build next.
See `wip/SESSION_LOG.md` for full history of what was done each session.
