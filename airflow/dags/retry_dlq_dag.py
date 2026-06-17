"""
Retry DLQ DAG

Scheduled hourly to consume from the 'dead_letter' topic,
re-run validations, load corrected items, and quarantine/archive failures.
"""

from __future__ import annotations

import sys
sys.path.insert(0, "/app")

import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

log = logging.getLogger(__name__)

DEFAULT_ARGS = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


def task_retry_dlq():
    """Executes the DLQ retry batch processor agent."""
    log.info("Starting DLQ retry processing task")
    from scripts import retry_dlq
    retry_dlq.main()
    log.info("DLQ retry processing task finished")


with DAG(
    dag_id="retry_dlq",
    description="Consumes from dead_letter topic and retries validations",
    default_args=DEFAULT_ARGS,
    schedule_interval="0 * * * *",  # Hourly
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["dlq", "retry", "postgres"],
) as dag:

    run_retry = PythonOperator(
        task_id="run_retry",
        python_callable=task_retry_dlq,
    )
