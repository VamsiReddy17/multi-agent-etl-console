"""
Streaming ETL DAG

Runs the Kafka → Transform → Quality → PostgreSQL pipeline every 5 minutes.
Each task maps to one agent stage so failures are isolated and retryable.
"""

from __future__ import annotations

import sys
sys.path.insert(0, "/app")
sys.path.insert(0, "/app/airflow/plugins")
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from kafka_topic_sensor import KafkaTopicSensor

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default args
# ---------------------------------------------------------------------------
DEFAULT_ARGS = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
    "retry_exponential_backoff": True,
    "email_on_failure": False,
    "email_on_retry": False,
}


# ---------------------------------------------------------------------------
# Task callables
# ---------------------------------------------------------------------------

def task_ingest(**context) -> dict:
    """Ingest a batch from Kafka and push result to XCom."""
    from agents.kafka_ingestion_agent import KafkaIngestionAgent

    agent = KafkaIngestionAgent()
    result = agent.run()
    agent.close()

    log.info(f"[ingest] rows={result['rows']} status={result['status']}")
    context["ti"].xcom_push(key="ingest_result", value=result)
    return result


def task_transform(**context) -> dict:
    """Transform ingested records."""
    from agents.transform_agent import TransformAgent

    ingest_result = context["ti"].xcom_pull(key="ingest_result", task_ids="ingest")
    if not ingest_result or ingest_result.get("rows", 0) == 0:
        log.info("[transform] No data to transform — skipping")
        return {"status": "skipped", "data": [], "rows": 0}

    agent = TransformAgent()
    result = agent.run(ingest_result)
    log.info(f"[transform] rows={result['rows']} status={result['status']}")
    context["ti"].xcom_push(key="transform_result", value=result)
    return result


def task_quality(**context) -> dict:
    """Validate transformed records."""
    from agents.quality_agent import QualityAgent

    transform_result = context["ti"].xcom_pull(key="transform_result", task_ids="transform")
    if not transform_result or transform_result.get("rows", 0) == 0:
        log.info("[quality] No data to validate — skipping")
        return {"status": "skipped", "data": [], "rows": 0, "quarantined": [], "quarantined_count": 0}

    agent = QualityAgent()
    result = agent.run(transform_result)
    log.info(
        f"[quality] valid={result['rows']} quarantined={result['quarantined_count']} "
        f"status={result['status']}"
    )
    context["ti"].xcom_push(key="quality_result", value=result)
    return result


def task_load(**context) -> dict:
    """Load valid records into PostgreSQL."""
    from agents.postgres_load_agent import PostgresLoadAgent

    quality_result = context["ti"].xcom_pull(key="quality_result", task_ids="quality")
    if not quality_result or quality_result.get("rows", 0) == 0:
        log.info("[load] No valid rows to load — skipping")
        return {"status": "skipped", "rows_loaded": 0}

    pipeline_start = datetime.now(timezone.utc)
    agent = PostgresLoadAgent()
    result = agent.run(quality_result, pipeline_start_time=pipeline_start)
    agent.close()

    log.info(f"[load] rows_loaded={result['rows_loaded']} status={result['status']}")
    if result["status"] != "success":
        raise RuntimeError(f"Load failed: {result.get('error_message')}")
    return result


def task_dlq(**context) -> dict:
    """Route quarantined records to the dead letter Kafka topic."""
    from agents.dead_letter_agent import DeadLetterAgent

    quality_result = context["ti"].xcom_pull(key="quality_result", task_ids="quality")
    if not quality_result or quality_result.get("quarantined_count", 0) == 0:
        log.info("[dlq] No quarantined records to route — skipping")
        return {"status": "skipped", "rows_sent": 0}

    agent = DeadLetterAgent()
    result = agent.run(quality_result)
    agent.close()

    log.info(f"[dlq] rows_sent={result['rows_sent']} status={result['status']}")
    if result["status"] == "error":
        raise RuntimeError(f"DLQ routing failed: {result.get('error_message')}")
    return result


# ---------------------------------------------------------------------------
# DAG definition
# ---------------------------------------------------------------------------
with DAG(
    dag_id="streaming_etl",
    description="Kafka → Transform → Quality → PostgreSQL streaming pipeline",
    default_args=DEFAULT_ARGS,
    schedule_interval="*/5 * * * *",   # Every 5 minutes
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["streaming", "etl", "kafka", "postgres"],
) as dag:

    wait_for_data = KafkaTopicSensor(
        task_id="wait_for_data",
        poke_interval=10,
        timeout=300,
        mode="poke",
    )

    ingest = PythonOperator(
        task_id="ingest",
        python_callable=task_ingest,
    )

    transform = PythonOperator(
        task_id="transform",
        python_callable=task_transform,
    )

    quality = PythonOperator(
        task_id="quality",
        python_callable=task_quality,
    )

    load = PythonOperator(
        task_id="load",
        python_callable=task_load,
    )

    dlq = PythonOperator(
        task_id="dlq",
        python_callable=task_dlq,
    )

    # Chain: wait_for_data → ingest → transform → quality → load & dlq
    wait_for_data >> ingest >> transform >> quality
    quality >> load
    quality >> dlq
