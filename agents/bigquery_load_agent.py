"""
BigQuery Load Agent

Inserts validated order events into warehouse.order_events in BigQuery
and logs each pipeline execution and quality report into BigQuery tables.

Features:
  - Dynamic JSON inserts via BigQuery SDK insert_rows_json
  - Robust exception handling and structured error reporting
  - Automatic UTC timestamp generation for metadata columns
  - Standard agent interface matching PostgresLoadAgent
"""

import logging
import time
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from google.cloud import bigquery
from google.oauth2 import service_account

from .config import PipelineConfig, default_config

logger = logging.getLogger(__name__)


class BigQueryLoadAgent:
    """
    Loads validated order events into GCP BigQuery.

    Usage:
        agent = BigQueryLoadAgent(config)
        result = agent.run(quality_result, pipeline_start_time)
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or default_config
        self.name = "BigQueryLoadAgent"
        self._client = None
        logger.setLevel(self.config.get_log_level())

    @property
    def client(self) -> bigquery.Client:
        """Lazily initialize BigQuery client."""
        if self._client is None:
            project_id = self.config.bq.project_id
            creds_path = self.config.bq.credentials_path

            if creds_path and os.path.exists(creds_path):
                logger.info(f"[BigQueryLoadAgent] Initializing client using key file: {creds_path}")
                self._client = bigquery.Client.from_service_account_json(creds_path, project=project_id)
            else:
                logger.info("[BigQueryLoadAgent] Initializing client using Application Default Credentials (ADC)")
                self._client = bigquery.Client(project=project_id)
        return self._client

    def _table_ref(self, table_name: str) -> str:
        """Resolve full BigQuery table ID."""
        dataset = self.config.bq.dataset
        project = self.client.project
        return f"{project}.{dataset}.{table_name}"

    def _iso_format(self, dt: Any) -> Optional[str]:
        """Convert datetime objects to standard ISO strings for BigQuery."""
        if isinstance(dt, datetime):
            return dt.isoformat()
        if isinstance(dt, str):
            return dt
        return None

    def run(
        self,
        input_result: Dict[str, Any],
        pipeline_start_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Load records from a quality result into BigQuery.

        Args:
            input_result: Result dict returned by QualityAgent.run()
            pipeline_start_time: When the overall pipeline run started

        Returns:
            Result dict with rows_loaded, duration, and status.
        """
        if input_result.get("status") not in ("success",):
            logger.warning("[BigQueryLoadAgent] Skipping — upstream status is not success")
            return self._result("skipped", 0, "Upstream failure", 0)

        records: List[Dict] = input_result.get("data", [])
        quarantined: List[Dict] = input_result.get("quarantined", [])
        if not records and not quarantined:
            logger.info("[BigQueryLoadAgent] No records to load or quarantine, skipping")
            return self._result("skipped", 0, None, 0)

        logger.info(f"[BigQueryLoadAgent] Loading {len(records)} records and {len(quarantined)} quarantined records into BigQuery")
        start = time.time()
        pipeline_start = pipeline_start_time or datetime.now(timezone.utc)

        rows_loaded = 0
        error_msg = None

        try:
            # Load Order Events
            if records:
                order_table = self._table_ref("order_events")
                cleaned_records = []
                for r in records:
                    cleaned_records.append({
                        "order_id": int(r["order_id"]) if r.get("order_id") is not None else None,
                        "customer_id": int(r["customer_id"]) if r.get("customer_id") is not None else None,
                        "product_id": int(r["product_id"]) if r.get("product_id") is not None else None,
                        "quantity": int(r["quantity"]) if r.get("quantity") is not None else None,
                        "amount": float(r["amount"]) if r.get("amount") is not None else None,
                        "event_type": r.get("event_type"),
                        "event_timestamp": self._iso_format(r.get("event_timestamp")),
                        "received_at": datetime.now(timezone.utc).isoformat(),
                        "processed": False
                    })
                
                logger.debug(f"[BigQueryLoadAgent] Pushing order_events: {cleaned_records}")
                errors = self.client.insert_rows_json(order_table, cleaned_records)
                if errors:
                    raise RuntimeError(f"Failed to insert order_events: {errors}")
                rows_loaded = len(records)

            # Load Quarantine Events
            if quarantined:
                quarantine_table = self._table_ref("quarantine_events")
                cleaned_quarantine = []
                for r in quarantined:
                    cleaned_quarantine.append({
                        "order_id": int(r["order_id"]) if r.get("order_id") is not None else None,
                        "customer_id": int(r["customer_id"]) if r.get("customer_id") is not None else None,
                        "product_id": int(r["product_id"]) if r.get("product_id") is not None else None,
                        "quantity": int(r["quantity"]) if r.get("quantity") is not None else None,
                        "amount": float(r["amount"] or r.get("total_amount") or 0.0),
                        "event_type": r.get("event_type"),
                        "event_timestamp": self._iso_format(r.get("event_timestamp")),
                        "error_message": r.get("error_message") or "Unknown validation error",
                        "quarantined_at": datetime.now(timezone.utc).isoformat(),
                        "resolved": False
                    })
                
                logger.debug(f"[BigQueryLoadAgent] Pushing quarantine_events: {cleaned_quarantine}")
                errors = self.client.insert_rows_json(quarantine_table, cleaned_quarantine)
                if errors:
                    raise RuntimeError(f"Failed to insert quarantine_events: {errors}")

            # Log execution stats
            pipeline_end = datetime.now(timezone.utc)
            duration_ms = (time.time() - start) * 1000

            execution_table = self._table_ref("pipeline_execution")
            execution_row = [{
                "pipeline_name": self.config.pipeline_name,
                "start_time": self._iso_format(pipeline_start),
                "end_time": self._iso_format(pipeline_end),
                "status": "success",
                "rows_processed": len(records) + len(quarantined),
                "error_message": None,
                "created_at": datetime.now(timezone.utc).isoformat()
            }]
            self.client.insert_rows_json(execution_table, execution_row)

            # Log quality report
            quality_table = self._table_ref("quality_report")
            total = len(records) + len(quarantined)
            err_rate = float((len(quarantined) / total) * 100) if total > 0 else 0.0
            quality_row = [{
                "pipeline_name": self.config.pipeline_name,
                "start_time": self._iso_format(pipeline_start),
                "end_time": self._iso_format(pipeline_end),
                "total_records": total,
                "valid_records": len(records),
                "quarantined_records": len(quarantined),
                "error_rate": err_rate,
                "created_at": datetime.now(timezone.utc).isoformat()
            }]
            self.client.insert_rows_json(quality_table, quality_row)

            logger.info(f"[BigQueryLoadAgent] Successfully loaded {rows_loaded} orders in {duration_ms:.2f}ms")
            return self._result("success", rows_loaded, None, duration_ms)

        except Exception as exc:
            error_msg = str(exc)
            logger.error(f"[BigQueryLoadAgent] Load error: {error_msg}")
            
            # Attempt to write error execution log
            try:
                pipeline_end = datetime.now(timezone.utc)
                execution_table = self._table_ref("pipeline_execution")
                execution_row = [{
                    "pipeline_name": self.config.pipeline_name,
                    "start_time": self._iso_format(pipeline_start),
                    "end_time": self._iso_format(pipeline_end),
                    "status": "error",
                    "rows_processed": 0,
                    "error_message": error_msg,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }]
                self.client.insert_rows_json(execution_table, execution_row)
            except Exception as inner_exc:
                logger.error(f"[BigQueryLoadAgent] Failed to log execution error: {inner_exc}")

            duration_ms = (time.time() - start) * 1000
            return self._result("error", 0, error_msg, duration_ms)

    def close(self):
        """Close connections or release client."""
        # BigQuery Client does not require explicit connection closure
        pass

    def _result(
        self,
        status: str,
        rows_loaded: int,
        error_message: Optional[str] = None,
        duration_ms: float = 0.0,
    ) -> Dict[str, Any]:
        return {
            "status": status,
            "rows_loaded": rows_loaded,
            "duration_ms": duration_ms,
            "error_message": error_message,
            "agent": self.name,
        }
