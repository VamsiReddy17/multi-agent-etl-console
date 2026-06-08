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
```
