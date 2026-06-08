"""
Transform Agent

Enriches and normalises raw Kafka messages before quality checks and loading.

Transformations applied:
  - Parse / coerce numeric fields (amount, quantity)
  - Add processed_at timestamp
  - Calculate total_amount = quantity * unit_price (if missing)
  - Normalise event_type to lowercase
  - Strip whitespace from string fields
  - Add pipeline metadata (_pipeline_name, _pipeline_version)
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .config import PipelineConfig, default_config

logger = logging.getLogger(__name__)

PIPELINE_VERSION = "1.0.0"


class TransformAgent:
    """
    Transforms raw order event dicts into enriched, normalised records.

    Usage:
        agent = TransformAgent(config)
        result = agent.run(raw_data)
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or default_config
        self.name = "TransformAgent"
        logger.setLevel(self.config.get_log_level())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, input_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform records from an ingestion result.

        Args:
            input_result: Result dict returned by KafkaIngestionAgent.run()

        Returns:
            Result dict with transformed data.
        """
        if input_result.get("status") != "success":
            logger.warning("[TransformAgent] Skipping — upstream status is not success")
            return self._result("skipped", [], [], "Upstream failure", 0)

        raw_records: List[Dict] = input_result.get("data", [])
        logger.info(f"[TransformAgent] Transforming {len(raw_records)} records")
        start = time.time()

        transformed = []
        errors = []

        for idx, record in enumerate(raw_records):
            try:
                transformed.append(self._transform_record(record))
            except Exception as exc:
                err = f"Record {idx} transform failed: {exc}"
                logger.warning(f"[TransformAgent] {err}")
                errors.append(err)

        duration = time.time() - start
        logger.info(
            f"[TransformAgent] {len(transformed)} transformed, "
            f"{len(errors)} failed in {duration:.2f}s"
        )
        return self._result("success", transformed, errors, None, duration)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _transform_record(self, record: Dict) -> Dict:
        """Apply all transformations to a single record."""
        out = dict(record)  # shallow copy

        # --- Coerce numeric types ---
        out["order_id"] = self._to_int(out.get("order_id"))
        out["customer_id"] = self._to_int(out.get("customer_id"))
        out["product_id"] = self._to_int(out.get("product_id"))
        out["quantity"] = self._to_int(out.get("quantity"), default=1)
        out["amount"] = self._to_float(out.get("amount", out.get("unit_price", 0.0)))
        out["unit_price"] = out["amount"]

        # --- Calculate total if missing ---
        if "total_amount" not in out or out["total_amount"] is None:
            qty = out.get("quantity") or 1
            price = out.get("unit_price") or 0.0
            out["total_amount"] = round(qty * price, 2)

        # --- Normalise strings ---
        if "event_type" in out:
            out["event_type"] = str(out["event_type"]).strip().lower()

        # --- Add timestamps ---
        now = datetime.now(timezone.utc).isoformat()
        out["processed_at"] = now
        if "event_timestamp" not in out or out["event_timestamp"] is None:
            out["event_timestamp"] = now

        # --- Pipeline metadata ---
        out["_pipeline_name"] = self.config.pipeline_name
        out["_pipeline_version"] = PIPELINE_VERSION

        return out

    @staticmethod
    def _to_int(value: Any, default: Optional[int] = None) -> Optional[int]:
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _to_float(value: Any, default: float = 0.0) -> float:
        try:
            return round(float(value), 4)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _result(
        status: str,
        data: List[Dict],
        errors: List[str],
        error_msg: Optional[str],
        duration: float,
    ) -> Dict[str, Any]:
        return {
            "status": status,
            "data": data,
            "rows": len(data),
            "duration_ms": round(duration * 1000, 2),
            "errors": errors,
            "error_message": error_msg,
            "agent": "TransformAgent",
        }
