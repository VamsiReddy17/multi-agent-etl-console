# BigQuery Migration Guide

This guide describes how to migrate and sync your local PostgreSQL data warehouse to Google Cloud BigQuery for cloud-scale production deployment, reporting, and analytics.

---

## 1. Schema Mapping & Datasets

Following the celestial/Cosmos theme, the BigQuery environment is organized into two distinct zones:

* **Raw Landing Zone (`nebula_raw_zone`)**: Replicates raw PostgreSQL transactional records, events, and metrics.
* **Analytics Layer (`solar_core_analytics`)**: Exposes cleaned dimension tables and reporting views optimized for visualization tools like Looker Studio.

### PostgreSQL → BigQuery Type Mapping

| PostgreSQL Type | BigQuery Type |
|----------------|--------------|
| `SERIAL` / `INTEGER` | `INT64` |
| `VARCHAR(n)` / `TEXT` | `STRING` |
| `DECIMAL(p, s)` | `NUMERIC` |
| `TIMESTAMP` | `TIMESTAMP` |
| `BOOLEAN` | `BOOL` |

---

## 2. Multi-Table Sync Strategy

Rather than syncing a single table, the system implements a complete data replication strategy transferring all 8 tables from PostgreSQL's `warehouse` schema to BigQuery:

| Postgres Table | BigQuery Raw Table | Sync Mode | Watermark Column |
| :--- | :--- | :--- | :--- |
| `warehouse.customers` | `nebula_raw_zone.customers` | **Full Overwrite** | None (Small lookup table) |
| `warehouse.products` | `nebula_raw_zone.products` | **Full Overwrite** | None (Small lookup table) |
| `warehouse.orders` | `nebula_raw_zone.orders` | **Incremental** | `created_at` |
| `warehouse.order_events` | `nebula_raw_zone.order_events` | **Incremental** | `received_at` |
| `warehouse.quarantine_events`| `nebula_raw_zone.quarantine_events`| **Incremental** | `quarantined_at` |
| `warehouse.permanent_failures` | `nebula_raw_zone.permanent_failures`| **Incremental** | `failed_at` |
| `warehouse.quality_report` | `nebula_raw_zone.quality_report` | **Incremental** | `created_at` |
| `warehouse.pipeline_execution` | `nebula_raw_zone.pipeline_execution`| **Incremental** | `created_at` |

### Replication Details:
1. **Full Overwrite (WRITE_TRUNCATE)**: Used for dimensional lookup tables (`customers`, `products`) to keep catalog metadata accurate and aligned with the source.
2. **Incremental (WRITE_APPEND)**: Uses watermarking timestamps to probe the target BigQuery table, retrieve the highest timestamp already loaded, and query PostgreSQL for only newer records (`WHERE watermark_column > max_watermark`).

---

## 3. Direct Streaming Injection (GCP Sandbox Constraint)

To support **GCP Free Sandbox Accounts** where Google Cloud Storage (GCS) buckets might trigger billing restriction errors (HTTP 403), both the historical backfill script and the Airflow sync DAG use **Direct Streaming Injection**:

1. **Extract**: Queries PostgreSQL using Python client libraries (`psycopg2` or Airflow's `PostgresHook`).
2. **Local Staging**: Formats rows as Newline-Delimited JSON (JSONL) and stages them locally in `/tmp/*.json` inside the worker container.
3. **Insert**: Uses the `google-cloud-bigquery` library's `load_table_from_file()` method to stream the staged JSONL directly to BigQuery over secure HTTPS, bypassing GCS completely.

---

## 4. Pipeline Code & SQL Configurations

### SQL Schemas & Transformations
* **Raw Schema Definitions**: Located under `bigquery/schema/*.sql` for each of the 8 tables.
* **Analytics View**: The reporting view `solar_core_analytics.orders_reporting` is defined in [reporting_views.sql](file:///Users/vamsireddy/Desktop/Agents%20Dev/production-pipeline/bigquery/transformations/reporting_views.sql) selecting from `nebula_raw_zone.order_events`.

### Historical Backfill Script
* **File**: [backfill_bigquery.py](file:///Users/vamsireddy/Desktop/Agents%20Dev/production-pipeline/scripts/backfill_bigquery.py)
* **Usage**: Runs a safe, chunked batch sync (50,000 rows per batch) to load all existing PostgreSQL records to BigQuery:
  ```bash
  .venv/bin/python scripts/backfill_bigquery.py
  ```

### Airflow Sync DAG
* **File**: [postgres_to_bigquery_sync.py](file:///Users/vamsireddy/Desktop/Agents%20Dev/production-pipeline/airflow/dags/postgres_to_bigquery_sync.py)
* **Execution**: Scheduled `@hourly` in Airflow. Dynamically loops over the configurations to build task dependencies (`sync_customers`, `sync_products`, etc.) and executes them concurrently.
