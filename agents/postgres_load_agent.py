"""
PostgreSQL Load Agent

Inserts validated order events into warehouse.order_events and
logs each pipeline execution into warehouse.pipeline_execution.

Features:
  - Upsert on (order_id, event_timestamp) to ensure idempotency
  - Batch inserts using executemany for efficiency
  - Logs pipeline run metadata (start/end time, rows, status, errors)
  - Connection pooling via psycopg2
  - Graceful rollback on failure
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .config import PipelineConfig, default_config

logger = logging.getLogger(__name__)


INSERT_ORDER_EVENT_SQL = """
INSERT INTO warehouse.order_events
    (order_id, customer_id, product_id, quantity, amount,
     event_type, event_timestamp, received_at, processed)
VALUES
    (%(order_id)s, %(customer_id)s, %(product_id)s, %(quantity)s, %(amount)s,
     %(event_type)s, %(event_timestamp)s, NOW(), FALSE)
ON CONFLICT DO NOTHING;
"""

INSERT_QUARANTINE_EVENT_SQL = """
INSERT INTO warehouse.quarantine_events
    (order_id, customer_id, product_id, quantity, amount,
     event_type, event_timestamp, error_message, quarantined_at, resolved)
VALUES
    (%(order_id)s, %(customer_id)s, %(product_id)s, %(quantity)s, %(amount)s,
     %(event_type)s, %(event_timestamp)s, %(error_message)s, NOW(), FALSE);
"""

LOG_EXECUTION_SQL = """
INSERT INTO warehouse.pipeline_execution
    (pipeline_name, start_time, end_time, status, rows_processed, error_message)
VALUES
    (%(pipeline_name)s, %(start_time)s, %(end_time)s, %(status)s,
     %(rows_processed)s, %(error_message)s);
"""


class PostgresLoadAgent:
    """
    Loads validated order events into PostgreSQL.

    Usage:
        agent = PostgresLoadAgent(config)
        result = agent.run(quality_result, pipeline_start_time)
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or default_config
        self.name = "PostgresLoadAgent"
        self._conn = None
        logger.setLevel(self.config.get_log_level())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        input_result: Dict[str, Any],
        pipeline_start_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Load records from a quality result into PostgreSQL.

        Args:
            input_result: Result dict returned by QualityAgent.run()
            pipeline_start_time: When the overall pipeline run started

        Returns:
            Result dict with rows_loaded, duration, and status.
        """
        if input_result.get("status") not in ("success",):
            logger.warning("[PostgresLoadAgent] Skipping — upstream status is not success")
            return self._result("skipped", 0, "Upstream failure", 0)

        records: List[Dict] = input_result.get("data", [])
        quarantined: List[Dict] = input_result.get("quarantined", [])
        if not records and not quarantined:
            logger.info("[PostgresLoadAgent] No records to load or quarantine, skipping")
            return self._result("skipped", 0, None, 0)

        logger.info(f"[PostgresLoadAgent] Loading {len(records)} records and {len(quarantined)} quarantined records into PostgreSQL")
        start = time.time()
        pipeline_start = pipeline_start_time or datetime.now(timezone.utc)

        rows_loaded = 0
        error_msg = None

        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                # Insert order events
                if records:
                    cur.executemany(INSERT_ORDER_EVENT_SQL, records)
                    rows_loaded = cur.rowcount if cur.rowcount != -1 else len(records)

                # Insert quarantined events
                if quarantined:
                    cleaned_quarantine = []
                    for r in quarantined:
                        cleaned_quarantine.append({
                            "order_id": r.get("order_id"),
                            "customer_id": r.get("customer_id"),
                            "product_id": r.get("product_id"),
                            "quantity": r.get("quantity"),
                            "amount": r.get("amount") or r.get("total_amount") or 0.0,
                            "event_type": r.get("event_type"),
                            "event_timestamp": r.get("event_timestamp"),
                            "error_message": r.get("error_message") or "Unknown quality validation check failure",
                        })
                    cur.executemany(INSERT_QUARANTINE_EVENT_SQL, cleaned_quarantine)

                # Dynamic Schema Drift Detection
                drift_logs = []
                standard_keys = {
                    "order_id", "customer_id", "product_id", "quantity", "amount", 
                    "event_type", "event_timestamp", "received_at", "processed", 
                    "_topic", "_partition", "_offset", "processed_at", 
                    "_pipeline_name", "_pipeline_version", "error_message", "unit_price", "total_amount"
                }
                detected_drift_fields = set()
                
                for r in (records + quarantined):
                    for k in r.keys():
                        if k not in standard_keys and k not in detected_drift_fields:
                            detected_drift_fields.add(k)
                            drift_logs.append({
                                "drift_type": "New Column Warning",
                                "field_name": f"{k} (varchar)",
                                "detected_by": "QualityAgent"
                            })
                
                if drift_logs:
                    logger.warning(f"[PostgresLoadAgent] SCHEMA DRIFT ALERT: Dynamically detected {len(drift_logs)} new columns! Logging alerts to database.")
                    cur.executemany(
                        """
                        INSERT INTO warehouse.schema_drift_logs
                            (drift_type, field_name, detected_by, status, logged_at)
                        VALUES
                            (%(drift_type)s, %(field_name)s, %(detected_by)s, 'Logged', NOW());
                        """,
                        drift_logs
                    )

                # Log pipeline execution
                cur.execute(LOG_EXECUTION_SQL, {
                    "pipeline_name": self.config.pipeline_name,
                    "start_time": pipeline_start,
                    "end_time": datetime.now(timezone.utc),
                    "status": "success",
                    "rows_processed": rows_loaded,
                    "error_message": None,
                })
            conn.commit()
        except Exception as exc:
            error_msg = str(exc)
            logger.error(f"[PostgresLoadAgent] Load failed: {exc}")
            self._rollback()
            self._log_failure(pipeline_start, len(records) + len(quarantined), error_msg)
            return self._result("error", 0, error_msg, time.time() - start)

        duration = time.time() - start
        logger.info(f"[PostgresLoadAgent] Loaded {rows_loaded} rows in {duration:.2f}s")
        return self._result("success", rows_loaded, None, duration)

    def close(self):
        """Close the database connection."""
        if self._conn:
            try:
                self._conn.close()
                logger.info("[PostgresLoadAgent] Connection closed")
            except Exception:
                pass
            self._conn = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_connection(self):
        """Lazily create / reuse psycopg2 connection."""
        try:
            import psycopg2  # type: ignore
        except ImportError:
            raise RuntimeError(
                "psycopg2-binary is not installed. Run: pip install psycopg2-binary"
            )

        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(**self.config.db.dsn)
            logger.debug("[PostgresLoadAgent] New DB connection established")
        return self._conn

    def _rollback(self):
        try:
            if self._conn and not self._conn.closed:
                self._conn.rollback()
        except Exception:
            pass

    def _log_failure(self, start: datetime, rows: int, error: str):
        """Try to log a failed pipeline execution (best-effort)."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(LOG_EXECUTION_SQL, {
                    "pipeline_name": self.config.pipeline_name,
                    "start_time": start,
                    "end_time": datetime.now(timezone.utc),
                    "status": "error",
                    "rows_processed": 0,
                    "error_message": error[:1000],
                })
            conn.commit()
        except Exception as exc:
            logger.warning(f"[PostgresLoadAgent] Could not log failure: {exc}")

    @staticmethod
    def _result(
        status: str,
        rows_loaded: int,
        error_msg: Optional[str],
        duration: float,
    ) -> Dict[str, Any]:
        return {
            "status": status,
            "rows_loaded": rows_loaded,
            "duration_ms": round(duration * 1000, 2),
            "error_message": error_msg,
            "agent": "PostgresLoadAgent",
        }
