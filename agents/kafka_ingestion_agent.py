"""
Kafka Ingestion Agent

Polls one or more Kafka topics and deserialises JSON messages into
a list of Python dicts ready for the downstream transform stage.

Features:
  - Configurable batch size and poll timeout
  - JSON deserialisation with error tolerance (bad messages are skipped & logged)
  - Returns AgentResult with row count and timing metrics
  - Graceful handling of connection errors
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

from .config import PipelineConfig, default_config

logger = logging.getLogger(__name__)


class KafkaIngestionAgent:
    """
    Ingests messages from one or more Kafka topics.

    Usage:
        agent = KafkaIngestionAgent(config)
        result = agent.run(topics=["orders"])
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or default_config
        self.name = "KafkaIngestionAgent"
        self._consumer = None
        logger.setLevel(self.config.get_log_level())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, topics: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Poll Kafka and return a batch of deserialised messages.

        Args:
            topics: List of topic names to subscribe to.
                    Defaults to config.kafka.topics.

        Returns:
            dict with keys: status, data, rows, duration_ms, errors
        """
        topics = topics or self.config.kafka.topics
        start = time.time()
        logger.info(f"[KafkaIngestionAgent] Subscribing to topics: {topics}")

        messages: List[Dict] = []
        errors: List[str] = []

        try:
            consumer = self._get_consumer(topics)
            messages, errors = self._poll_batch(consumer)
        except Exception as exc:
            logger.error(f"[KafkaIngestionAgent] Connection error: {exc}")
            return self._result("error", [], [], str(exc), time.time() - start)

        duration = time.time() - start
        logger.info(
            f"[KafkaIngestionAgent] Ingested {len(messages)} messages "
            f"({len(errors)} skipped) in {duration:.2f}s"
        )
        return self._result("success", messages, errors, None, duration)

    def close(self):
        """Close the Kafka consumer."""
        if self._consumer:
            try:
                self._consumer.close()
                logger.info("[KafkaIngestionAgent] Consumer closed")
            except Exception:
                pass
            self._consumer = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_consumer(self, topics: List[str]):
        """Lazily create / reuse KafkaConsumer."""
        try:
            from kafka import KafkaConsumer  # type: ignore
        except ImportError:
            raise RuntimeError(
                "kafka-python is not installed. Run: pip install kafka-python"
            )

        if self._consumer is None:
            self._consumer = KafkaConsumer(
                *topics,
                bootstrap_servers=self.config.kafka.broker,
                group_id=self.config.kafka.group_id,
                auto_offset_reset=self.config.kafka.auto_offset_reset,
                enable_auto_commit=True,
                value_deserializer=lambda m: m,   # raw bytes; we parse below
                consumer_timeout_ms=self.config.kafka.poll_timeout_ms,
            )
        else:
            self._consumer.subscribe(topics)
        return self._consumer

    def _poll_batch(self, consumer) -> tuple:
        """Poll up to batch_size messages from the consumer."""
        messages = []
        errors = []
        limit = self.config.kafka.batch_size

        for raw_msg in consumer:
            try:
                payload = json.loads(raw_msg.value.decode("utf-8"))
                payload.setdefault("_topic", raw_msg.topic)
                payload.setdefault("_partition", raw_msg.partition)
                payload.setdefault("_offset", raw_msg.offset)
                messages.append(payload)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                err = f"Failed to decode message offset={raw_msg.offset}: {exc}"
                logger.warning(f"[KafkaIngestionAgent] {err}")
                errors.append(err)

            if len(messages) >= limit:
                break

        return messages, errors

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
            "agent": "KafkaIngestionAgent",
        }
