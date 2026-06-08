"""
Unit and Integration Tests for Prometheus Metrics

Verifies that metrics are correctly defined, exposed, and updated during
pipeline execution stages without requiring live Kafka or Postgres services.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipelines.streaming_etl import (
    StreamingETL,
    PIPELINE_RUNS_TOTAL,
    ROWS_PROCESSED_TOTAL,
    ROWS_QUARANTINED_TOTAL,
    PIPELINE_DURATION_SECONDS,
    STAGE_DURATION_SECONDS
)


class TestStreamingETLMetrics:

    @patch("pipelines.streaming_etl.KafkaIngestionAgent")
    @patch("pipelines.streaming_etl.TransformAgent")
    @patch("pipelines.streaming_etl.QualityAgent")
    @patch("pipelines.streaming_etl.PostgresLoadAgent")
    def test_metrics_updated_on_success(self, mock_load, mock_quality, mock_transform, mock_ingestion):
        """Verify that all counters and summaries are correctly updated on success."""
        
        # Read starting metric values to calculate deltas
        runs_before = PIPELINE_RUNS_TOTAL.labels(status="success")._value.get()
        rows_ingest_before = ROWS_PROCESSED_TOTAL.labels(stage="ingestion")._value.get()
        rows_transform_before = ROWS_PROCESSED_TOTAL.labels(stage="transform")._value.get()
        rows_quality_before = ROWS_PROCESSED_TOTAL.labels(stage="quality")._value.get()
        rows_load_before = ROWS_PROCESSED_TOTAL.labels(stage="load")._value.get()
        quarantined_before = ROWS_QUARANTINED_TOTAL._value.get()

        # Mock Kafka Ingestion Stage
        mock_ingestion_inst = mock_ingestion.return_value
        mock_ingestion_inst.run.return_value = {
            "status": "success",
            "rows": 3,
            "data": [{"order_id": 1}, {"order_id": 2}, {"order_id": 3}],
            "duration_ms": 100.0,
            "agent": "KafkaIngestionAgent"
        }

        # Mock Transform Stage
        mock_transform_inst = mock_transform.return_value
        mock_transform_inst.run.return_value = {
            "status": "success",
            "rows": 3,
            "data": [{"order_id": 1}, {"order_id": 2}, {"order_id": 3}],
            "duration_ms": 50.0,
            "agent": "TransformAgent"
        }

        # Mock Quality Stage (5 valid, 1 quarantined)
        mock_quality_inst = mock_quality.return_value
        mock_quality_inst.run.return_value = {
            "status": "success",
            "rows": 5,
            "quarantined_count": 1,
            "data": [{"order_id": 1}, {"order_id": 2}, {"order_id": 3}, {"order_id": 4}, {"order_id": 5}],
            "duration_ms": 40.0,
            "agent": "QualityAgent"
        }

        # Mock PostgreSQL Load Stage
        mock_load_inst = mock_load.return_value
        mock_load_inst.run.return_value = {
            "status": "success",
            "rows_loaded": 5,
            "duration_ms": 80.0,
            "agent": "PostgresLoadAgent"
        }

        # Execute single pipeline run
        pipeline = StreamingETL()
        result = pipeline.run_once()

        assert result["status"] == "success"

        # Assert metrics updated correctly
        assert PIPELINE_RUNS_TOTAL.labels(status="success")._value.get() - runs_before == 1
        assert ROWS_PROCESSED_TOTAL.labels(stage="ingestion")._value.get() - rows_ingest_before == 3
        assert ROWS_PROCESSED_TOTAL.labels(stage="transform")._value.get() - rows_transform_before == 3
        assert ROWS_PROCESSED_TOTAL.labels(stage="quality")._value.get() - rows_quality_before == 5
        assert ROWS_PROCESSED_TOTAL.labels(stage="load")._value.get() - rows_load_before == 5
        assert ROWS_QUARANTINED_TOTAL._value.get() - quarantined_before == 1

    @patch("pipelines.streaming_etl.KafkaIngestionAgent")
    def test_metrics_updated_on_no_data(self, mock_ingestion):
        """Verify metrics are updated correctly when Kafka is empty."""
        
        runs_before = PIPELINE_RUNS_TOTAL.labels(status="no_data")._value.get()
        rows_ingest_before = ROWS_PROCESSED_TOTAL.labels(stage="ingestion")._value.get()

        mock_ingestion_inst = mock_ingestion.return_value
        mock_ingestion_inst.run.return_value = {
            "status": "success",
            "rows": 0,
            "data": [],
            "duration_ms": 10.0,
            "agent": "KafkaIngestionAgent"
        }

        pipeline = StreamingETL()
        result = pipeline.run_once()

        assert result["status"] == "no_data"
        assert PIPELINE_RUNS_TOTAL.labels(status="no_data")._value.get() - runs_before == 1
        assert ROWS_PROCESSED_TOTAL.labels(stage="ingestion")._value.get() - rows_ingest_before == 0
