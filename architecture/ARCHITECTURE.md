# Architecture Guide

## Overview

The production pipeline is a **multi-agent data engineering system** that streams order events from Apache Kafka, processes them through 4 specialised agents, and loads clean data into a PostgreSQL data warehouse. Apache Airflow orchestrates and schedules all runs.

![Architecture Diagram](./architecture_diagram.png)

---

## System Components

### 1. Data Sources
External systems publish JSON events to Kafka topics. Examples:
- E-commerce order management systems
- IoT sensors
- Third-party APIs
- Manual test producers

### 2. Apache Kafka (Message Broker)
**Role**: Decouples data producers from the pipeline.
**Port**: `9092`
**Topics**:

| Topic | Purpose |
|-------|---------|
| `orders` | New and updated order events |
| `customers` | Customer profile updates |
| `products` | Product catalog changes |
| `events` | Generic application events |
| `enriched_orders` | Processed output (future use) |

Kafka guarantees durability and allows the pipeline to replay messages if needed.

### 3. Multi-Agent Pipeline

The heart of the system — 4 agents run in sequence, each with a single responsibility:

#### Agent 1 — Kafka Ingestion Agent
- **File**: `agents/kafka_ingestion_agent.py`
- **Input**: Kafka topics
- **Output**: List of raw Python dicts
- **Responsibility**: Poll Kafka, decode JSON, handle malformed messages gracefully
- **Key feature**: Configurable batch size; bad JSON is skipped and logged, not crashed

#### Agent 2 — Transform Agent
- **File**: `agents/transform_agent.py`
- **Input**: Raw dicts from ingestion
- **Output**: Enriched, normalised dicts
- **Responsibility**: Type coercion, total amount calculation, timestamp injection, string normalisation
- **Key feature**: All transformations are deterministic and idempotent

#### Agent 3 — Quality Agent
- **File**: `agents/quality_agent.py`
- **Input**: Enriched dicts from transform
- **Output**: Two sets — valid records + quarantined records
- **Responsibility**: Validate fields, ranges, duplicates, and known event types
- **Key feature**: Configurable quarantine threshold — aborts load if too many bad records

#### Agent 4 — PostgreSQL Load Agent
- **File**: `agents/postgres_load_agent.py`
- **Input**: Valid records from quality
- **Output**: Load summary with row count and timing
- **Responsibility**: Batch insert to `warehouse.order_events`, log run to `warehouse.pipeline_execution`
- **Key feature**: Idempotent upsert (ON CONFLICT DO NOTHING), graceful rollback on failure

### 4. PostgreSQL Data Warehouse
**Port**: `5432`
**Database**: `dataware`
**Schema**: `warehouse`

| Table | Purpose |
|-------|---------|
| `customers` | Customer dimension |
| `products` | Product dimension |
| `orders` | Orders fact table |
| `order_events` | Streaming events from Kafka |
| `pipeline_execution` | Audit log of every pipeline run |

### 5. Apache Airflow (Orchestrator)
**Port**: `8080` (Web UI)
**Executor**: Celery (backed by Redis)

| DAG | Schedule | Tasks |
|-----|----------|-------|
| `streaming_etl` | Every 5 minutes | ingest → transform → quality → load |
| `batch_orders_etl` | Daily midnight | extract → validate → mark_processed → log |

### 6. Redis
**Port**: `6379`
**Role**: Celery task queue backend for Airflow workers. Enables distributed task execution.

---

## Deployment Topology

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│                                                          │
│  ┌──────────┐   ┌──────────┐   ┌──────────────────┐    │
│  │Zookeeper │──▶│  Kafka   │──▶│ Agent Pipeline   │    │
│  │ :2181    │   │  :9092   │   │ (Python process) │    │
│  └──────────┘   └──────────┘   └────────┬─────────┘    │
│                                          │               │
│  ┌──────────┐   ┌──────────┐            ▼               │
│  │  Redis   │──▶│ Airflow  │   ┌──────────────────┐    │
│  │  :6379   │   │  :8080   │   │   PostgreSQL     │    │
│  └──────────┘   └──────────┘   │     :5432        │    │
│                                 └──────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## Failure Handling

| Failure | How Handled |
|---------|-------------|
| Bad JSON in Kafka | Skipped + logged, rest of batch continues |
| Transform error on a record | Skipped + logged, rest of batch continues |
| Too many quarantined records | Pipeline aborts before load (configurable threshold) |
| PostgreSQL insert failure | Transaction rolled back, failure logged to `pipeline_execution` |
| Airflow task failure | Auto-retried up to 2x with exponential backoff |
| Kafka connection down | Returns error result, Airflow retries the task |

---

## Scalability

| Dimension | Current (Local) | Production Path |
|-----------|----------------|-----------------|
| Message throughput | ~100 msgs/batch | Increase `KAFKA_BATCH_SIZE` |
| Pipeline frequency | Every 5 min | Adjust Airflow schedule |
| Parallel workers | 1 Celery worker | Add more `airflow_worker` containers |
| Storage | Local PostgreSQL | Migrate to BigQuery (see `docs/BIGQUERY_MIGRATION.md`) |
| Messaging | Local Kafka | Migrate to Google Cloud Pub/Sub |
