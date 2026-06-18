# Airflow Orchestration Guide

Apache Airflow is the central orchestration engine of the Multi-Agent ETL stack, scheduling, monitoring, and managing task executions.

---

## 🏗️ High-Level Airflow Task Architecture

Airflow runs in a Celery-Executor topology utilizing Redis as a task queue broker and PostgreSQL as the database metadata store. The system runs two key pipelines:

```
1. streaming_etl DAG (Runs every 5 minutes)
┌──────────────────────┐     ┌─────────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│ wait_for_kafka_data  │ ──► │  ingest_from_kafka  │ ──► │  transform_events │ ──► │ quality_assertion │
└──────────────────────┘     └─────────────────────┘     └───────────────────┘     └─────────┬─────────┘
                                                                                             │
                                                                           ┌─────────────────┴─────────────────┐
                                                                           │ (Clean)                           │ (Anomaly)
                                                                           ▼                                   ▼
                                                                 ┌───────────────────┐               ┌───────────────────┐
                                                                 │   load_to_store   │               │     route_dlq     │
                                                                 └───────────────────┘               └───────────────────┘

2. postgres_to_bigquery_sync DAG (Runs hourly)
┌──────────────────────┐     ┌─────────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│    sync_customers    │     │    sync_products    │     │    sync_orders    │     │ sync_order_events │
└──────────────────────┘     └─────────────────────┘     └───────────────────┘     └───────────────────┘
   (Full Overwrite)             (Full Overwrite)            (Incremental)               (Incremental)
                                     ... (syncs all 8 tables concurrently)
```

---

## ⚙️ Active DAGs & Component Roles

### 1. `streaming_etl`
Ingests events from Kafka, runs transformations, asserts quality, and loads clean outputs.
* **`wait_for_kafka_data` (Custom Sensor)**: Invokes our custom `KafkaTopicSensor` to probe partition lag offsets. If there are no new unconsumed messages, it pauses and defers the run to save compute.
* **`ingest_from_kafka`**: Calls `KafkaIngestionAgent` to pull batches of up to 2000 messages from the topic.
* **`transform_events`**: Calls `TransformAgent` to enrich data, parse typings, and calculate totals.
* **`quality_assertion`**: Calls `QualityAgent` to check values and schema compliance.
* **`load_to_store`**: Dynamically switches target databases based on `LOAD_TARGET` (loads locally to `warehouse.order_events` or streams to BQ raw zone).
* **`route_dlq`**: Invokes `DeadLetterAgent` to route quarantined payloads to a segregated Kafka topic.

### 2. `postgres_to_bigquery_sync`
Orchestrates replication of all 8 database tables from local PostgreSQL to the BigQuery cloud dataset `nebula_raw_zone`.
* **Watermarked Sync**: Probes the BigQuery target to query `MAX(watermark_column)`, then retrieves only newer rows from PostgreSQL to guarantee no duplicate inserts.
* **Overwrite Sync**: Truncates and updates lookup tables (`customers`, `products`) to ensure catalog matching.

---

## 🛠️ CLI Operations

### Enabling DAGs
To unpause DAGs via the CLI:
```bash
docker exec prod_airflow_webserver airflow dags unpause streaming_etl
docker exec prod_airflow_webserver airflow dags unpause postgres_to_bigquery_sync
```

### Triggering a Sync Run Manually
```bash
docker exec prod_airflow_webserver airflow dags trigger postgres_to_bigquery_sync
```

### Checking Task Failures or Logs
If a run fails:
1. Open the Airflow Web UI at http://localhost:8080.
2. Click on the DAG (e.g. `postgres_to_bigquery_sync`) and select **Grid** or **Graph** view.
3. Click the failed task box, and select the **Logs** tab to troubleshoot.
