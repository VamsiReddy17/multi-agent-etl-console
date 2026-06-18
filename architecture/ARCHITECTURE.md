# Architecture Guide — Multi-Agent Cosmos Pipeline

## Overview

The production pipeline is a high-throughput, production-ready **multi-agent data engineering system** running in a hybrid local-to-cloud architecture. It streams order events from Apache Kafka, validates and processes them through cooperative Python-based AI agents, orchestrates batch and incremental pipelines using Apache Airflow, exposes control routes via FastAPI, and replicates data into a Google Cloud BigQuery data warehouse.

The frontend is styled as **The Cosmos** — a premium, celestial-themed single-page React dashboard detailing sessions, metrics, topology, and anomalies.

---

## 🏗️ End-to-End System Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   Local PC (Docker Host)                               │
│                                                                                        │
│  ┌──────────────────┐      ┌──────────────┐      ┌─────────────┐      ┌─────────────┐  │
│  │ Order Generator  │ ───► │ Apache Kafka │ ───► │ Ingestion   │ ───► │ Transform   │  │
│  │ (python script)  │      │   (:9092)    │      │ Agent       │      │ Agent       │  │
│  └──────────────────┘      └──────────────┘      └─────────────┘      └──────┬──────┘  │
│                                                                              │         │
│  ┌──────────────────┐      ┌──────────────┐      ┌─────────────┐             │         │
│  │   FastAPI API    │      │  PostgreSQL  │ ◄─── │ Load Agent  │ ◄─── ┌──────┴──────┐  │
│  │     (:8081)      │      │   (:5432)    │      │ (Postgres)  │      │Quality Agent│  │
│  └──────────────────┘      └──────────────┘      └─────────────┘      └──────┬──────┘  │
│                                                                              │         │
│  ┌──────────────────┐      ┌──────────────┐      ┌─────────────┐             │         │
│  │   Airflow Web    │ ◄─── │ Airflow Worker │ ◄─ │ Load Agent  │ ◄───────────┘         │
│  │   & Scheduler    │      │   (Celery)   │      │ (BigQuery)  │                       │
│  │     (:8080)      │      └──────────────┘      └──────┬──────┘                       │
│  └──────────────────┘                                   │                             │
└─────────────────────────────────────────────────────────┼──────────────────────────────┘
                                                          │ (Outbound HTTPS REST calls
                                                          │  using Application Credentials)
                                                          ▼
                                            ┌───────────────────────────┐
                                            │     Google Cloud GCP      │
                                            │                           │
                                            │ ┌───────────────────────┐ │
                                            │ │   BigQuery Dataset    │ │
                                            │ │  (nebula_raw_zone)    │ │
                                            │ └──────────┬────────────┘ │
                                            │            │              │
                                            │ ┌──────────▼────────────┐ │
                                            │ │     Reporting View    │ │
                                            │ │(solar_core_analytics) │ │
                                            │ └───────────────────────┘ │
                                            └───────────────────────────┘
```

---

## ☁️ Hybrid Local-to-Cloud Integration Strategy

Although your database, ingestion messaging broker, and pipeline schedulers are hosted locally inside Docker on your PC, the analytical storage layer resides in Google Cloud BigQuery. We bridge these environments seamlessly using a **Secure HTTPS Client-Server Integration**:

1. **Authentication (ADC)**: We generated Google Application Default Credentials (ADC) locally using the Google Cloud SDK (`gcloud auth application-default login`). These credentials are mounted securely into the Airflow scheduler, webserver, and worker containers:
   - `- ~/.config/gcloud:/root/.config/gcloud:ro`
2. **Network Connection**: Even though the containers are running inside a local Docker network, they have outbound internet access through your host PC's network. They communicate with Google Cloud over secure HTTPS.
3. **BigQuery Python Client**: The python tasks use the official GCP library (`google-cloud-bigquery`). The library automatically detects the mounted ADC credentials, opens an HTTPS stream to `https://bigquery.googleapis.com`, and inserts/overwrites the data directly.
4. **Local Staging Bypass**: To support free GCP Sandbox accounts with disabled billing, the pipeline writes records locally as Newline-Delimited JSON (JSONL) inside `/tmp/` within the container, and streams them directly into BigQuery via `load_table_from_file()`, completely bypassing GCS.

---

## 🛠️ System Components & Achieved Progress

### 1. Multi-Agent ETL Orchestration
Four cooperative, single-responsibility Python agents process batches of streaming data:
* **Ingestion Agent** (`agents/kafka_ingestion_agent.py`): Polls Kafka topics, handles malformed payloads gracefully, and emits clean python dict arrays.
* **Transform Agent** (`agents/transform_agent.py`): Enriches records, calculates order totals, normalizes strings, and adds execution timestamps.
* **Quality Agent** (`agents/quality_agent.py`): Asserts data rules (field ranges, schema checks, duplicates), quarantining anomalies. Aborts the load stage if the quarantine rate exceeds 20%.
* **Load Agents**: 
  - **Postgres Load Agent** (`agents/postgres_load_agent.py`): Performs bulk inserts to `warehouse.order_events` and logs metrics to `warehouse.quality_report`.
  - **BigQuery Load Agent** (`agents/bigquery_load_agent.py`): Performs batch loading directly into BigQuery tables, utilizing dynamic type serialization.

### 2. Dual-Target Ingestion Switching
Controlled via the `LOAD_TARGET` environment variable:
- `postgres`: Loads data locally into PostgreSQL.
- `bigquery`: Streams data directly to GCP BigQuery tables under `nebula_raw_zone`.

### 3. Change Data Capture & Multi-Table Replication
We achieved a complete data replication strategy transferring all 8 tables in the PostgreSQL `warehouse` schema to BigQuery:
- **Dimensions (Overwrite)**: `customers` and `products` are overwritten via `WRITE_TRUNCATE` during sync, preserving metadata lookup accuracy.
- **Facts (Incremental)**: `orders`, `order_events`, `quarantine_events`, `permanent_failures`, `quality_report`, and `pipeline_execution` are loaded incrementally based on watermark fields (e.g., `received_at`, `created_at`).
- **Watermarking**: The Airflow DAG queries the highest timestamp from BigQuery first, then extracts only newer records from PostgreSQL, preventing duplication.

### 4. FastAPI Control & Orchestration Layer (`prod_api` service)
Exposes endpoint controls on host port `8081` to manage and monitor the pipeline state:
- `GET /health`: Validates endpoint status.
- `POST /pipeline/run`: Triggers a single ETL batch run and returns processing statistics.
- `GET /pipeline/status`: Dynamically queries the active load target (Postgres or BigQuery) to return execution stats.

### 5. Automated Pipeline Safety
* **Custom Airflow Sensor (`KafkaTopicSensor`)**: Probes topic partition log offsets dynamically to verify consumer lag without consuming or advancing offsets, pausing execution when lag is zero.
* **Dead Letter Queue (DLQ)**: The `DeadLetterAgent` routes quarantined records to a `dead_letter` Kafka topic for isolation, preventing pipeline blockages.

### 6. Cosmos Telemetry Dashboard
Vite + React single-page dashboard displaying the celestial theme:
- **The Nebula**: Sessions timeline.
- **The Asteroid Belt**: Error logging and RCA.
- **The Solar Core**: Bento-grid telemetry stats and custom interactive SVG charts with hover snap lines, area glow gradients, and toggling legends.
- **The Event Horizon**: Sandbox editor to review and re-run quarantined payloads.
