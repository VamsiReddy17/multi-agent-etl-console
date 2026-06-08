"""
Batch Orders DAG

Runs a daily batch job at midnight that:
  1. Queries unprocessed order_events from PostgreSQL
  2. Re-validates them through the QualityAgent
  3. Marks them as processed and logs execution metrics

This handles any events that may have been missed by the streaming pipeline.
"""

from __future__ import annotations

import sys
import logging
from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

sys.path.insert(0, "/app")

log = logging.getLogger(__name__)

DEFAULT_ARGS = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
    "email_on_retry": False,
}

POSTGRES_CONN_ID = "postgres_default"


# ---------------------------------------------------------------------------
# Task callables
# ---------------------------------------------------------------------------

def task_extract_unprocessed(**context) -> dict:
    """Fetch all unprocessed order events from PostgreSQL."""
    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    sql = """
        SELECT
            event_id, order_id, customer_id, product_id,
            quantity, amount, event_type, event_timestamp
        FROM warehouse.order_events
        WHERE processed = FALSE
        ORDER BY event_timestamp ASC
        LIMIT 10000;
    """
    records = hook.get_records(sql)
    columns = [
        "event_id", "order_id", "customer_id", "product_id",
        "quantity", "amount", "event_type", "event_timestamp",
    ]
    rows = [dict(zip(columns, r)) for r in records]
    log.info(f"[batch_extract] Found {len(rows)} unprocessed events")
    result = {"status": "success", "data": rows, "rows": len(rows)}
    context["ti"].xcom_push(key="extract_result", value=result)
    return result


def task_validate_batch(**context) -> dict:
    """Re-run quality checks on unprocessed events."""
    from agents.quality_agent import QualityAgent

    extract_result = context["ti"].xcom_pull(key="extract_result", task_ids="extract_unprocessed")
    if not extract_result or extract_result.get("rows", 0) == 0:
        log.info("[batch_validate] No unprocessed events — nothing to do")
        return {"status": "skipped", "data": [], "rows": 0, "quarantined": [], "quarantined_count": 0}

    agent = QualityAgent()
    result = agent.run(extract_result)
    log.info(
        f"[batch_validate] valid={result['rows']} "
        f"quarantined={result['quarantined_count']}"
    )
    context["ti"].xcom_push(key="quality_result", value=result)
    return result


def task_mark_processed(**context) -> dict:
    """Mark validated events as processed in PostgreSQL."""
    quality_result = context["ti"].xcom_pull(key="quality_result", task_ids="validate_batch")
    if not quality_result or quality_result.get("rows", 0) == 0:
        log.info("[batch_mark] No valid rows — skipping")
        return {"status": "skipped", "rows_updated": 0}

    valid_records = quality_result.get("data", [])
    event_ids = [r["event_id"] for r in valid_records if r.get("event_id")]

    if not event_ids:
        return {"status": "skipped", "rows_updated": 0}

    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    placeholders = ",".join(["%s"] * len(event_ids))
    sql = f"""
        UPDATE warehouse.order_events
        SET processed = TRUE
        WHERE event_id IN ({placeholders});
    """
    hook.run(sql, parameters=event_ids)
    log.info(f"[batch_mark] Marked {len(event_ids)} events as processed")
    return {"status": "success", "rows_updated": len(event_ids)}


def task_log_batch_run(**context) -> None:
    """Log the batch run outcome to pipeline_execution."""
    quality_result = context["ti"].xcom_pull(key="quality_result", task_ids="validate_batch") or {}
    rows = quality_result.get("rows", 0)

    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    hook.run(
        """
        INSERT INTO warehouse.pipeline_execution
            (pipeline_name, start_time, end_time, status, rows_processed, error_message)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        parameters=(
            "batch-orders-etl",
            context["data_interval_start"],
            datetime.now(timezone.utc),
            "success",
            rows,
            None,
        ),
    )
    log.info(f"[batch_log] Logged batch run: {rows} rows processed")


# ---------------------------------------------------------------------------
# DAG definition
# ---------------------------------------------------------------------------
with DAG(
    dag_id="batch_orders_etl",
    description="Daily batch — reprocess unprocessed order events from PostgreSQL",
    default_args=DEFAULT_ARGS,
    schedule_interval="0 0 * * *",   # Daily at midnight
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["batch", "etl", "postgres", "orders"],
) as dag:

    extract = PythonOperator(
        task_id="extract_unprocessed",
        python_callable=task_extract_unprocessed,
    )

    validate = PythonOperator(
        task_id="validate_batch",
        python_callable=task_validate_batch,
    )

    mark = PythonOperator(
        task_id="mark_processed",
        python_callable=task_mark_processed,
    )

    log_run = PythonOperator(
        task_id="log_batch_run",
        python_callable=task_log_batch_run,
    )

    extract >> validate >> mark >> log_run
