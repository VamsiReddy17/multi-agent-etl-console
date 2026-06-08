# Airflow Guide

## Accessing the UI

Open http://localhost:8080 — login with `airflow / airflow`

---

## Available DAGs

| DAG ID | Schedule | Description |
|--------|----------|-------------|
| `streaming_etl` | Every 5 min | Kafka → Transform → Quality → PostgreSQL |
| `batch_orders_etl` | Daily midnight | Reprocess unprocessed order events |

---

## Enabling DAGs

DAGs are paused by default. Enable via:

1. Open http://localhost:8080
2. Find the DAG in the list
3. Toggle the **On/Off** switch on the left

Or via CLI:
```bash
docker exec prod_airflow_webserver airflow dags unpause streaming_etl
docker exec prod_airflow_webserver airflow dags unpause batch_orders_etl
```

---

## Triggering a DAG Manually

```bash
# Via CLI
docker exec prod_airflow_webserver airflow dags trigger streaming_etl

# Via UI
# Click the ▶ (Trigger) button on the DAG row
```

---

## Viewing Logs

```bash
# Scheduler logs
docker-compose logs -f airflow_scheduler

# Worker logs
docker-compose logs -f airflow_worker
```

---

## Adding the PostgreSQL Connection

For the `batch_orders_etl` DAG, add a connection in Airflow:

1. Go to **Admin → Connections**
2. Click **+** (Add connection)
3. Fill in:
   - **Conn ID**: `postgres_default`
   - **Conn Type**: `Postgres`
   - **Host**: `postgres`
   - **Schema**: `dataware`
   - **Login**: `postgres`
   - **Password**: `postgres_password`
   - **Port**: `5432`

Or via CLI:
```bash
docker exec prod_airflow_webserver airflow connections add postgres_default \
  --conn-type postgres \
  --conn-host postgres \
  --conn-schema dataware \
  --conn-login postgres \
  --conn-password postgres_password \
  --conn-port 5432
```

---

## Monitoring Pipeline Executions

```sql
-- Connect to PostgreSQL and check logs
SELECT pipeline_name, start_time, end_time, status, rows_processed
FROM warehouse.pipeline_execution
ORDER BY created_at DESC
LIMIT 20;
```
