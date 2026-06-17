"""
FastAPI REST API Layer

Exposes HTTP endpoints to:
  - Trigger single-batch pipeline execution on-demand (/pipeline/run)
  - Inspect latest execution status from postgres/BigQuery (/pipeline/status)
  - Verify service health (/health)
"""

import os
import logging
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException

from pipelines.streaming_etl import StreamingETL
from agents.config import PipelineConfig

logger = logging.getLogger("api_server")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Cosmos ETL Monitoring & Control API",
    description="REST API for triggering and inspecting the Multi-Agent ETL Pipeline",
    version="1.0.0"
)


@app.get("/health")
def health():
    """Returns the API service health status and timestamp."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/pipeline/run")
def trigger_run():
    """Triggers a single ETL batch run and returns the run summary."""
    try:
        logger.info("[API] Triggering manual pipeline run")
        pipeline = StreamingETL()
        summary = pipeline.run_once()
        return summary
    except Exception as exc:
        logger.exception("[API] Failed to run pipeline manually")
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline execution encountered error: {exc}"
        )


@app.get("/pipeline/status")
def get_status():
    """Fetches the metadata of the latest execution from the active load target."""
    config = PipelineConfig()
    logger.info(f"[API] Fetching latest status from target: {config.load_target}")

    if config.load_target == "bigquery":
        try:
            from google.cloud import bigquery
            client = bigquery.Client(project=config.bq.project_id)
            dataset = config.bq.dataset
            table_ref = f"{client.project}.{dataset}.pipeline_execution"

            query = f"""
                SELECT pipeline_name, start_time, end_time, status, rows_processed, error_message
                FROM `{table_ref}`
                ORDER BY start_time DESC
                LIMIT 1
            """
            query_job = client.query(query)
            results = list(query_job.result())

            if not results:
                return {"message": "No pipeline executions found in BigQuery."}

            row = results[0]
            return {
                "pipeline_name": row.get("pipeline_name"),
                "start_time": row.get("start_time").isoformat() if hasattr(row.get("start_time"), "isoformat") else row.get("start_time"),
                "end_time": row.get("end_time").isoformat() if hasattr(row.get("end_time"), "isoformat") else row.get("end_time"),
                "status": row.get("status"),
                "rows_processed": row.get("rows_processed"),
                "error_message": row.get("error_message")
            }
        except Exception as exc:
            logger.exception("[API] Failed to query BigQuery execution status")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch execution log from BigQuery: {exc}"
            )
    else:
        # Default to postgres
        try:
            import psycopg2
            conn = psycopg2.connect(**config.db.dsn)
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT pipeline_name, start_time, end_time, status, rows_processed, error_message
                    FROM warehouse.pipeline_execution
                    ORDER BY execution_id DESC
                    LIMIT 1;
                """)
                row = cur.fetchone()
                if not row:
                    return {"message": "No pipeline executions found in PostgreSQL."}

                return {
                    "pipeline_name": row[0],
                    "start_time": row[1].isoformat() if hasattr(row[1], "isoformat") else row[1],
                    "end_time": row[2].isoformat() if hasattr(row[2], "isoformat") else row[2],
                    "status": row[3],
                    "rows_processed": row[4],
                    "error_message": row[5]
                }
            conn.close()
        except Exception as exc:
            logger.exception("[API] Failed to query PostgreSQL execution status")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch execution log from PostgreSQL: {exc}"
            )
