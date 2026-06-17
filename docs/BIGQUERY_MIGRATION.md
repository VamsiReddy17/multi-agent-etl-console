# BigQuery Migration Guide

## Overview

This guide describes how to migrate the production pipeline from local PostgreSQL to Google BigQuery for cloud-scale production deployment.

---

## Schema Migration

### PostgreSQL → BigQuery Mapping

| PostgreSQL Type | BigQuery Type |
|----------------|--------------|
| `SERIAL` | `INT64` (auto-assigned by app) |
| `VARCHAR(n)` | `STRING` |
| `DECIMAL(p, s)` | `NUMERIC` |
| `TIMESTAMP` | `TIMESTAMP` |
| `BOOLEAN` | `BOOL` |

### BigQuery Dataset Setup

```bash
bq mk --dataset \
  --location=US \
  your-project:warehouse
```

### Create Tables

```sql
-- order_events
CREATE TABLE warehouse.order_events (
  event_id INT64,
  order_id INT64,
  customer_id INT64,
  product_id INT64,
  quantity INT64,
  amount NUMERIC,
  event_type STRING,
  event_timestamp TIMESTAMP,
  received_at TIMESTAMP,
  processed BOOL
);
```

---

## Agent Updates

### Replace `PostgresLoadAgent` with BigQuery Load Agent

```python
from google.cloud import bigquery

class BigQueryLoadAgent:
    def __init__(self, project_id: str, dataset: str):
        self.client = bigquery.Client(project=project_id)
        self.table_id = f"{project_id}.{dataset}.order_events"

    def run(self, quality_result):
        rows = quality_result["data"]
        errors = self.client.insert_rows_json(self.table_id, rows)
        if errors:
            raise RuntimeError(f"BigQuery insert errors: {errors}")
        return {"status": "success", "rows_loaded": len(rows)}
```

---

## Kafka → BigQuery via Pub/Sub (Recommended)

For production, replace Kafka with **Google Cloud Pub/Sub**:

```
Pub/Sub Topic → Dataflow (streaming) → BigQuery
```

Or use **Kafka Connect BigQuery Sink Connector**:

```bash
# Deploy Kafka Connect with BigQuery sink
curl -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d '{
    "name": "bigquery-sink",
    "config": {
      "connector.class": "com.wepay.kafka.connect.bigquery.BigQuerySinkConnector",
      "topics": "orders,customers",
      "project": "your-project",
      "datasets": ".*=warehouse",
      "keyfile": "/path/to/service-account.json"
    }
  }'
```

---

## Airflow on Cloud Composer

Replace local Airflow with **Google Cloud Composer**:

1. Create a Composer environment in GCP Console
2. Upload DAGs to the Composer GCS bucket
3. Update connection IDs to use GCP service accounts

```bash
gsutil cp airflow/dags/*.py gs://your-composer-bucket/dags/
```

---

## Environment Variables for BigQuery

```env
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCP_PROJECT_ID=your-project-id
BQ_DATASET=warehouse
PUBSUB_TOPIC_ORDERS=projects/your-project/topics/orders

---

## PostgreSQL to BigQuery ELT Sync (Batch Replication)

For cost-effective free-tier data warehousing and Looker Studio reporting, a batch ELT pipeline is implemented to sync PostgreSQL order events incrementally into Google BigQuery:

### 1. Watermark Sync DAG
- **DAG File**: [postgres_to_bigquery_sync.py](file:///Users/vamsireddy/Desktop/Agents%20Dev/production-pipeline/airflow/dags/postgres_to_bigquery_sync.py)
- **Replication Flow**:
  1. **Watermark Probe**: Queries the target BigQuery table `raw.order_events` to retrieve the latest `received_at` timestamp.
  2. **Incremental Extract**: Queries PostgreSQL table `warehouse.order_events` where `received_at > last_watermark` and saves it locally in JSON lines format.
  3. **Stage**: Uploads the JSON lines file to Google Cloud Storage (GCS).
  4. **Load**: Triggers BigQuery to bulk load the staged JSON lines from GCS into the `raw.order_events` table.

### 2. BigQuery Transformations (T in ELT)
SQL definitions and dimensional views are located in:
- [order_events.sql](file:///Users/vamsireddy/Desktop/Agents%20Dev/production-pipeline/bigquery/schema/order_events.sql)
- [reporting_views.sql](file:///Users/vamsireddy/Desktop/Agents%20Dev/production-pipeline/bigquery/transformations/reporting_views.sql)

Looker Studio connects directly to the reporting view `warehouse.orders_reporting` to render metrics without running queries on the raw table.
```
