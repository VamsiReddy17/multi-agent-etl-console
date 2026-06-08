"""
Quality Agent

Validates transformed records before they are loaded into PostgreSQL.

Checks applied:
  - Required fields are present (order_id, customer_id, amount)
  - Numeric fields are within acceptable ranges (amount > 0, quantity >= 1)
  - customer_id and product_id are positive integers
  - No duplicate order_ids within the batch
  - event_type is a known value (if provided)

Records that fail validation are quarantined (removed from the good set)
and their errors are reported in the result.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Set

from .config import PipelineConfig, default_config

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = ["order_id", "customer_id", "amount"]
KNOWN_EVENT_TYPES = {"order_placed", "order_updated", "order_cancelled", "order_completed", ""}
MAX_AMOUNT = 1_000_000.0


class QualityAgent:
    """
    Validates a batch of transformed order event records.

    Usage:
        agent = QualityAgent(config)
        result = agent.run(transform_result)
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or default_config
        self.name = "QualityAgent"
        logger.setLevel(self.config.get_log_level())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, input_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate records from a transform result.

        Args:
            input_result: Result dict returned by TransformAgent.run()

        Returns:
            Result dict with only valid records in 'data', quarantined
            records in 'quarantined', and all validation errors listed.
        """
        if input_result.get("status") not in ("success",):
            logger.warning("[QualityAgent] Skipping — upstream status is not success")
            return self._result("skipped", [], [], [], "Upstream failure", 0)

        records: List[Dict] = input_result.get("data", [])
        logger.info(f"[QualityAgent] Validating {len(records)} records")
        start = time.time()

        valid: List[Dict] = []
        quarantined: List[Dict] = []
        all_errors: List[str] = []
        seen_order_ids: Set = set()

        for idx, record in enumerate(records):
            errors = self._validate(record, seen_order_ids)
            if errors:
                record_copy = dict(record)
                record_copy["error_message"] = "; ".join(errors)
                quarantined.append(record_copy)
                for err in errors:
                    msg = f"Record {idx} (order_id={record.get('order_id')}): {err}"
                    logger.warning(f"[QualityAgent] ⚠ {msg}")
                    all_errors.append(msg)
            else:
                valid.append(record)
                if record.get("order_id") is not None:
                    seen_order_ids.add(record["order_id"])

        duration = time.time() - start
        logger.info(
            f"[QualityAgent] {len(valid)} valid, {len(quarantined)} quarantined "
            f"in {duration:.2f}s"
        )
        return self._result("success", valid, quarantined, all_errors, None, duration)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _validate(self, record: Dict, seen_ids: Set) -> List[str]:
        """Return list of validation error strings (empty = valid)."""
        errors = []

        # Required fields
        for field in REQUIRED_FIELDS:
            if record.get(field) is None:
                errors.append(f"Missing required field: '{field}'")

        if errors:
            return errors  # skip numeric checks if required fields missing

        # Amount range
        amount = record.get("amount", 0)
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            errors.append(f"Invalid amount value: {amount!r}")
            amount = 0

        if amount <= 0:
            errors.append(f"Amount must be > 0, got {amount}")
        if amount > MAX_AMOUNT:
            errors.append(f"Amount {amount} exceeds maximum {MAX_AMOUNT}")

        # Quantity
        qty = record.get("quantity", 1)
        try:
            qty = int(qty)
        except (ValueError, TypeError):
            qty = 0
        if qty < 1:
            errors.append(f"Quantity must be >= 1, got {qty}")

        # Positive IDs
        for id_field in ("customer_id", "product_id"):
            val = record.get(id_field)
            if val is not None:
                try:
                    if int(val) <= 0:
                        errors.append(f"'{id_field}' must be a positive integer, got {val}")
                except (ValueError, TypeError):
                    errors.append(f"'{id_field}' is not a valid integer: {val!r}")

        # Duplicate order_id within batch
        oid = record.get("order_id")
        if oid is not None and oid in seen_ids:
            errors.append(f"Duplicate order_id {oid} within batch")

        # Known event_type
        etype = str(record.get("event_type", "")).lower()
        if etype and etype not in KNOWN_EVENT_TYPES:
            errors.append(f"Unknown event_type: '{etype}'")

        return errors

    @staticmethod
    def _result(
        status: str,
        data: List[Dict],
        quarantined: List[Dict],
        errors: List[str],
        error_msg: Optional[str],
        duration: float,
    ) -> Dict[str, Any]:
        return {
            "status": status,
            "data": data,
            "rows": len(data),
            "quarantined": quarantined,
            "quarantined_count": len(quarantined),
            "duration_ms": round(duration * 1000, 2),
            "errors": errors,
            "error_message": error_msg,
            "agent": "QualityAgent",
        }
