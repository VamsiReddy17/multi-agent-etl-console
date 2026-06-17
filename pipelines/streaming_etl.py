"""
Streaming ETL Pipeline

Orchestrates the full multi-agent pipeline:
  KafkaIngestionAgent → TransformAgent → QualityAgent → PostgresLoadAgent

Can run as:
  - Single batch:  StreamingETL().run_once()
  - Continuous:    StreamingETL().run_loop()
  - CLI:           python -m pipelines.streaming_etl

Usage:
    from pipelines.streaming_etl import StreamingETL
    pipeline = StreamingETL()
    pipeline.run_once()
"""

import logging
import sys
import time
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from prometheus_client import start_http_server, Counter, Summary

# Prometheus Metrics Definition
PIPELINE_RUNS_TOTAL = Counter(
    "pipeline_runs_total",
    "Total runs of the streaming ETL pipeline",
    ["status"]
)
ROWS_PROCESSED_TOTAL = Counter(
    "rows_processed_total",
    "Total rows processed by pipeline stages",
    ["stage"]
)
ROWS_QUARANTINED_TOTAL = Counter(
    "rows_quarantined_total",
    "Total rows quarantined due to quality failures"
)
PIPELINE_DURATION_SECONDS = Summary(
    "pipeline_duration_seconds",
    "End-to-end pipeline execution time in seconds"
)
STAGE_DURATION_SECONDS = Summary(
    "stage_duration_seconds",
    "Execution time of each pipeline stage in seconds",
    ["stage"]
)

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.config import PipelineConfig
from agents.kafka_ingestion_agent import KafkaIngestionAgent
from agents.transform_agent import TransformAgent
from agents.quality_agent import QualityAgent
from agents.postgres_load_agent import PostgresLoadAgent
from agents.dead_letter_agent import DeadLetterAgent

logger = logging.getLogger("streaming_etl")

CONFIG_PATH = Path(__file__).parent / "config" / "pipeline_config.yaml"


def _load_yaml_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f) or {}
    return {}


class StreamingETL:
    """
    Orchestrates the Kafka → Transform → Quality → Postgres pipeline.
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self.yaml_cfg = _load_yaml_config()

        # Setup logging
        log_level = getattr(
            logging,
            self.yaml_cfg.get("pipeline", {}).get("log_level", "INFO"),
            logging.INFO,
        )
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Propagate YAML config to self.config properties to ensure settings like batch_size apply
        if "kafka" in self.yaml_cfg:
            k_cfg = self.yaml_cfg["kafka"]
            if "batch_size" in k_cfg:
                self.config.kafka.batch_size = int(k_cfg["batch_size"])
            if "poll_timeout_ms" in k_cfg:
                self.config.kafka.poll_timeout_ms = int(k_cfg["poll_timeout_ms"])

        if "pipeline" in self.yaml_cfg:
            p_cfg = self.yaml_cfg["pipeline"]
            if "max_retries" in p_cfg:
                self.config.max_retries = int(p_cfg["max_retries"])
            if "retry_delay_seconds" in p_cfg:
                self.config.retry_delay_seconds = int(p_cfg["retry_delay_seconds"])

        # Instantiate agents
        self.ingestion = KafkaIngestionAgent(self.config)
        self.transform = TransformAgent(self.config)
        self.quality = QualityAgent(self.config)
        
        # Select loader target dynamically
        if self.config.load_target == "bigquery":
            from agents.bigquery_load_agent import BigQueryLoadAgent
            if BigQueryLoadAgent is None:
                raise ImportError("BigQueryLoadAgent is not available. Please install google-cloud-bigquery.")
            self.load = BigQueryLoadAgent(self.config)
        else:
            self.load = PostgresLoadAgent(self.config)

        self.dead_letter = DeadLetterAgent(self.config)

        # Pipeline config
        p = self.yaml_cfg.get("pipeline", {})
        self.poll_interval = p.get("poll_interval_seconds", 5)
        self.max_empty_polls = self.yaml_cfg.get("kafka", {}).get("max_empty_polls", 10)
        self.quarantine_threshold = self.yaml_cfg.get("quality", {}).get(
            "quarantine_threshold", 0.2
        )

    def get_kafka_lag(self) -> int:
        """
        Calculate total consumer lag across all topics.
        """
        lag = 0
        try:
            consumer = self.ingestion._get_consumer(self.config.kafka.topics)
            for topic in self.config.kafka.topics:
                partitions = consumer.partitions_for_topic(topic)
                if not partitions:
                    continue
                from kafka import TopicPartition
                tps = [TopicPartition(topic, p) for p in partitions]
                end_offsets = consumer.end_offsets(tps)
                for tp in tps:
                    latest = end_offsets.get(tp, 0)
                    try:
                        current = consumer.position(tp)
                    except Exception:
                        current = 0
                    lag += max(0, latest - current)
        except Exception as e:
            logger.warning(f"[StreamingETL] Could not calculate Kafka lag: {e}")
        return lag

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_once(self, topics: Optional[list] = None) -> dict:
        """
        Execute a single pipeline batch.

        Returns a summary dict with status and metrics from each stage.
        """
        # Referee Ingestion Controller: dynamic throughput adjustment
        lag = self.get_kafka_lag()
        base_batch_size = int(self.yaml_cfg.get("kafka", {}).get("batch_size", 100))
        
        if lag > 1000:
            self.config.kafka.batch_size = base_batch_size * 5
            logger.warning(f"[Referee Controller] Backlog spiked ({lag} messages). Boosting throughput size: {self.config.kafka.batch_size}!")
        elif lag > 200:
            self.config.kafka.batch_size = base_batch_size * 2
            logger.info(f"[Referee Controller] Lag detected ({lag} messages). Escalating throughput size: {self.config.kafka.batch_size}.")
        else:
            self.config.kafka.batch_size = base_batch_size
            logger.info(f"[Referee Controller] Lag healthy ({lag} messages). Throughput size: {self.config.kafka.batch_size}.")

        pipeline_start = datetime.now(timezone.utc)
        banner = "=" * 65
        print(f"\n{banner}")
        print("  STREAMING ETL PIPELINE — SINGLE RUN")
        print(f"  Started: {pipeline_start.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"{banner}\n")

        # Stage 1: Ingest
        print("▶ Stage 1/4 — Kafka Ingestion")
        ingest_result = self.ingestion.run(topics=topics)
        self._print_stage_result(ingest_result)

        STAGE_DURATION_SECONDS.labels(stage="ingestion").observe(ingest_result.get("duration_ms", 0) / 1000.0)
        ROWS_PROCESSED_TOTAL.labels(stage="ingestion").inc(ingest_result.get("rows", 0))

        if ingest_result["rows"] == 0:
            print("  ℹ No messages available in Kafka topics — nothing to process.\n")
            PIPELINE_RUNS_TOTAL.labels(status="no_data").inc()
            PIPELINE_DURATION_SECONDS.observe((datetime.now(timezone.utc) - pipeline_start).total_seconds())
            return self._summary(pipeline_start, "no_data", [ingest_result])

        # Stage 2: Transform
        print("▶ Stage 2/4 — Transform")
        transform_result = self.transform.run(ingest_result)
        self._print_stage_result(transform_result)

        STAGE_DURATION_SECONDS.labels(stage="transform").observe(transform_result.get("duration_ms", 0) / 1000.0)
        ROWS_PROCESSED_TOTAL.labels(stage="transform").inc(transform_result.get("rows", 0))

        if transform_result["status"] != "success":
            PIPELINE_RUNS_TOTAL.labels(status="failed").inc()
            PIPELINE_DURATION_SECONDS.observe((datetime.now(timezone.utc) - pipeline_start).total_seconds())
            return self._summary(pipeline_start, "failed", [ingest_result, transform_result])

        # Stage 3: Quality
        print("▶ Stage 3/4 — Quality")
        quality_result = self.quality.run(transform_result)
        self._print_stage_result(quality_result)

        # Dead Letter Queue Routing
        if quality_result.get("quarantined_count", 0) > 0:
            print("▶ Stage 3b/4 — Dead Letter Queue Routing")
            dlq_result = self.dead_letter.run(quality_result)
            self._print_stage_result(dlq_result)

        STAGE_DURATION_SECONDS.labels(stage="quality").observe(quality_result.get("duration_ms", 0) / 1000.0)
        ROWS_PROCESSED_TOTAL.labels(stage="quality").inc(quality_result.get("rows", 0))
        ROWS_QUARANTINED_TOTAL.inc(quality_result.get("quarantined_count", 0))

        # Check quarantine threshold
        total = quality_result["rows"] + quality_result["quarantined_count"]
        if total > 0:
            quarantine_rate = quality_result["quarantined_count"] / total
            if quarantine_rate > self.quarantine_threshold:
                msg = (
                    f"Quarantine rate {quarantine_rate:.1%} exceeds threshold "
                    f"{self.quarantine_threshold:.1%} — aborting load"
                )
                logger.error(f"[StreamingETL] {msg}")
                print(f"  ✗ {msg}\n")
                PIPELINE_RUNS_TOTAL.labels(status="failed").inc()
                PIPELINE_DURATION_SECONDS.observe((datetime.now(timezone.utc) - pipeline_start).total_seconds())
                return self._summary(
                    pipeline_start, "failed", [ingest_result, transform_result, quality_result]
                )

        if quality_result["rows"] == 0:
            print("  ℹ All records quarantined — skipping load.\n")
            PIPELINE_RUNS_TOTAL.labels(status="quarantined").inc()
            PIPELINE_DURATION_SECONDS.observe((datetime.now(timezone.utc) - pipeline_start).total_seconds())
            return self._summary(
                pipeline_start, "quarantined",
                [ingest_result, transform_result, quality_result]
            )

        # Stage 4: Load
        target_label = "BigQuery" if self.config.load_target == "bigquery" else "PostgreSQL"
        print(f"▶ Stage 4/4 — {target_label} Load")
        load_result = self.load.run(quality_result, pipeline_start_time=pipeline_start)
        self._print_stage_result(load_result)

        STAGE_DURATION_SECONDS.labels(stage="load").observe(load_result.get("duration_ms", 0) / 1000.0)
        ROWS_PROCESSED_TOTAL.labels(stage="load").inc(load_result.get("rows_loaded", 0))

        overall = "success" if load_result["status"] == "success" else "failed"
        PIPELINE_RUNS_TOTAL.labels(status=overall).inc()
        PIPELINE_DURATION_SECONDS.observe((datetime.now(timezone.utc) - pipeline_start).total_seconds())
        return self._summary(
            pipeline_start, overall,
            [ingest_result, transform_result, quality_result, load_result]
        )

    def run_loop(self, topics: Optional[list] = None):
        """
        Run pipeline in a continuous loop, polling Kafka repeatedly.

        Stops after max_empty_polls consecutive empty polls (if > 0).
        Press Ctrl+C to stop manually.
        """
        logger.info("[StreamingETL] Starting continuous loop mode")
        
        try:
            start_http_server(8000)
            logger.info("[StreamingETL] Prometheus metrics server started on port 8000")
        except Exception as e:
            logger.warning(f"[StreamingETL] Prometheus metrics server failed to start: {e}")

        empty_polls = 0
        batch_num = 0

        try:
            while True:
                batch_num += 1
                logger.info(f"[StreamingETL] === Batch #{batch_num} ===")
                summary = self.run_once(topics=topics)

                if summary["status"] == "no_data":
                    empty_polls += 1
                    if self.max_empty_polls > 0 and empty_polls >= self.max_empty_polls:
                        logger.info(
                            f"[StreamingETL] {empty_polls} consecutive empty polls — stopping"
                        )
                        break
                else:
                    empty_polls = 0

                logger.info(f"[StreamingETL] Sleeping {self.poll_interval}s before next batch")
                time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            logger.info("[StreamingETL] Loop interrupted by user")
        finally:
            self._cleanup()
            logger.info("[StreamingETL] Pipeline stopped")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _cleanup(self):
        """Close all agent connections."""
        self.ingestion.close()
        self.load.close()
        self.dead_letter.close()

    @staticmethod
    def _print_stage_result(result: dict):
        status_icon = "✓" if result["status"] == "success" else ("⚠" if result["status"] == "skipped" else "✗")
        rows = result.get("rows", result.get("rows_loaded", "—"))
        ms = result.get("duration_ms", 0)
        agent = result.get("agent", "")
        print(f"  {status_icon} {agent}: {rows} rows | {ms:.0f}ms | status={result['status']}")
        if result.get("errors"):
            for err in result["errors"][:3]:
                print(f"    ⚠ {err}")
        print()

    @staticmethod
    def _summary(start: datetime, status: str, stage_results: list) -> dict:
        end = datetime.now(timezone.utc)
        total_ms = (end - start).total_seconds() * 1000
        banner = "=" * 65
        status_icon = "✅" if status == "success" else ("ℹ️" if status in ("no_data", "quarantined") else "❌")
        print(f"{banner}")
        print(f"  PIPELINE STATUS: {status_icon} {status.upper()}")
        print(f"  Total time: {total_ms:.0f}ms")
        print(f"{banner}\n")
        return {
            "status": status,
            "started_at": start.isoformat(),
            "ended_at": end.isoformat(),
            "total_ms": round(total_ms, 2),
            "stages": stage_results,
        }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Streaming ETL Pipeline")
    parser.add_argument(
        "--mode",
        choices=["once", "loop"],
        default="once",
        help="Run a single batch ('once') or continuously ('loop')",
    )
    parser.add_argument(
        "--topics",
        nargs="+",
        default=None,
        help="Kafka topic names to consume (overrides config)",
    )
    args = parser.parse_args()

    pipeline = StreamingETL()

    if args.mode == "loop":
        pipeline.run_loop(topics=args.topics)
    else:
        result = pipeline.run_once(topics=args.topics)
        sys.exit(0 if result["status"] in ("success", "no_data") else 1)
