"""
End-to-End Pipeline Integration Test

Tests the full agent chain: Ingest → Transform → Quality → Load
without requiring live Kafka or PostgreSQL connections.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.config import PipelineConfig
from agents.transform_agent import TransformAgent
from agents.quality_agent import QualityAgent
from agents.postgres_load_agent import PostgresLoadAgent


@pytest.fixture
def config():
    return PipelineConfig()


def _mock_ingest_result(records):
    """Simulate a successful KafkaIngestionAgent result."""
    return {
        "status": "success",
        "data": records,
        "rows": len(records),
        "duration_ms": 12.5,
        "errors": [],
        "error_message": None,
        "agent": "KafkaIngestionAgent",
    }


def _mock_conn():
    cursor = MagicMock()
    cursor.__enter__ = lambda s: cursor
    cursor.__exit__ = MagicMock(return_value=False)
    cursor.rowcount = -1
    conn = MagicMock()
    conn.closed = False
    conn.cursor.return_value = cursor
    return conn, cursor


SAMPLE_RECORDS = [
    {"order_id": "1", "customer_id": "101", "product_id": "1",
     "quantity": "2", "amount": "49.99", "event_type": "order_placed"},
    {"order_id": "2", "customer_id": "102", "product_id": "2",
     "quantity": "1", "amount": "29.99", "event_type": "order_completed"},
    {"order_id": "3", "customer_id": "103", "product_id": "3",
     "quantity": "1", "amount": "0",        # ← bad: amount=0, will be quarantined
     "event_type": "order_placed"},
]


class TestFullPipeline:

    def test_happy_path_two_valid_one_quarantined(self, config):
        """2 valid + 1 invalid record: 2 make it to load."""
        ingest = _mock_ingest_result(SAMPLE_RECORDS)

        transform_agent = TransformAgent(config)
        transform_result = transform_agent.run(ingest)
        assert transform_result["status"] == "success"
        assert transform_result["rows"] == 3

        quality_agent = QualityAgent(config)
        quality_result = quality_agent.run(transform_result)
        assert quality_result["status"] == "success"
        assert quality_result["rows"] == 2
        assert quality_result["quarantined_count"] == 1

        load_agent = PostgresLoadAgent(config)
        conn, cursor = _mock_conn()
        load_agent._conn = conn

        load_result = load_agent.run(quality_result, pipeline_start_time=datetime.now(timezone.utc))
        assert load_result["status"] == "success"
        assert cursor.executemany.call_count == 2

    def test_all_bad_records_nothing_loaded(self, config):
        """All records fail quality — load is skipped."""
        bad_records = [
            {"order_id": i, "customer_id": 1, "amount": 0}  # amount=0 fails
            for i in range(1, 4)
        ]
        ingest = _mock_ingest_result(bad_records)

        transform_result = TransformAgent(config).run(ingest)
        quality_result = QualityAgent(config).run(transform_result)
        assert quality_result["rows"] == 0
        assert quality_result["quarantined_count"] == 3

        load_agent = PostgresLoadAgent(config)
        conn, cursor = _mock_conn()
        load_agent._conn = conn
        load_result = load_agent.run(quality_result)
        assert load_result["status"] == "success"
        assert load_result["rows_loaded"] == 0
        assert cursor.executemany.call_count == 1

    def test_empty_ingest_skips_all_stages(self, config):
        """Empty Kafka poll short-circuits the whole chain gracefully."""
        ingest = _mock_ingest_result([])

        transform_result = TransformAgent(config).run(ingest)
        # Transform succeeds with 0 rows — quality still runs
        quality_result = QualityAgent(config).run(transform_result)
        assert quality_result["rows"] == 0

        load_result = PostgresLoadAgent(config).run(quality_result)
        assert load_result["status"] == "skipped"

    def test_type_coercion_flows_through(self, config):
        """String IDs/amounts from Kafka are properly coerced before loading."""
        ingest = _mock_ingest_result([{
            "order_id": "99", "customer_id": "200",
            "product_id": "3", "quantity": "5",
            "amount": "100.50", "event_type": "order_placed",
        }])

        transform_result = TransformAgent(config).run(ingest)
        rec = transform_result["data"][0]
        assert rec["order_id"] == 99
        assert rec["customer_id"] == 200
        assert rec["quantity"] == 5
        assert rec["amount"] == 100.5
        assert rec["total_amount"] == 502.5

    @patch("agents.bigquery_load_agent.bigquery.Client")
    def test_happy_path_bigquery_target(self, mock_client_class, config):
        """Pipeline executes successfully when target is BigQuery."""
        config.load_target = "bigquery"
        config.bq.project_id = "test-project"
        config.bq.dataset = "test_dataset"

        mock_client = MagicMock()
        mock_client.project = "test-project"
        mock_client.insert_rows_json.return_value = []
        mock_client_class.return_value = mock_client

        from pipelines.streaming_etl import StreamingETL
        pipeline = StreamingETL(config)
        pipeline.quarantine_threshold = 1.0
        
        # Mock Ingest results
        pipeline.ingestion.run = MagicMock(return_value=_mock_ingest_result(SAMPLE_RECORDS))
        
        summary = pipeline.run_once()
        assert summary["status"] == "success"
        
        # Verify stages
        stages = {s["agent"]: s for s in summary["stages"]}
        assert "KafkaIngestionAgent" in stages
        assert "TransformAgent" in stages
        assert "QualityAgent" in stages
        assert "BigQueryLoadAgent" in stages
        
        assert stages["BigQueryLoadAgent"]["rows_loaded"] == 2
        assert mock_client.insert_rows_json.call_count == 4
