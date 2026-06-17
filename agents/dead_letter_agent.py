"""
Dead Letter Agent

Routes quarantined records to a dead letter topic in Kafka.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

from .config import PipelineConfig, default_config

logger = logging.getLogger(__name__)


class DeadLetterAgent:
    """
    Publishes quarantined records to the dead letter queue (dead_letter topic).
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or default_config
        self.name = "DeadLetterAgent"
        self._producer = None
        logger.setLevel(self.config.get_log_level())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, input_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Produce quarantined records to Kafka.

        Args:
            input_result: Result dict returned by QualityAgent.run()

        Returns:
            dict with keys: status, rows_sent, duration_ms, errors
        """
        if input_result.get("status") not in ("success",):
            logger.warning("[DeadLetterAgent] Skipping — upstream status is not success")
            return self._result("skipped", 0, "Upstream failure", 0)

        quarantined: List[Dict] = input_result.get("quarantined", [])
        if not quarantined:
            logger.info("[DeadLetterAgent] No quarantined records to route")
            return self._result("success", 0, None, 0)

        start = time.time()
        dlq_topic = "dead_letter"
        logger.info(f"[DeadLetterAgent] Routing {len(quarantined)} records to topic '{dlq_topic}'")

        try:
            producer = self._get_producer()
            for record in quarantined:
                # Send copy of the record with error metadata
                producer.send(dlq_topic, record)
            producer.flush()
        except Exception as exc:
            logger.error(f"[DeadLetterAgent] Failed to route to DLQ: {exc}")
            return self._result("error", 0, str(exc), time.time() - start)

        duration = time.time() - start
        logger.info(
            f"[DeadLetterAgent] Routed {len(quarantined)} quarantined records "
            f"in {duration:.2f}s"
        )
        return self._result("success", len(quarantined), None, duration)

    def close(self):
        """Close the Kafka producer connection."""
        if self._producer:
            try:
                self._producer.close()
                logger.info("[DeadLetterAgent] Producer closed")
            except Exception:
                pass
            self._producer = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_producer(self):
        """Lazily create / reuse KafkaProducer."""
        try:
            from kafka import KafkaProducer  # type: ignore
        except ImportError:
            raise RuntimeError(
                "kafka-python is not installed. Run: pip install kafka-python"
            )

        if self._producer is None:
            self._producer = KafkaProducer(
                bootstrap_servers=self.config.kafka.broker,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
        return self._producer

    @staticmethod
    def _result(
        status: str,
        rows_sent: int,
        error_msg: Optional[str],
        duration: float,
    ) -> Dict[str, Any]:
        return {
            "status": status,
            "rows_sent": rows_sent,
            "rows": rows_sent, # for standard print_stage_result
            "duration_ms": round(duration * 1000, 2),
            "errors": [error_msg] if error_msg else [],
            "error_message": error_msg,
            "agent": "DeadLetterAgent",
        }
