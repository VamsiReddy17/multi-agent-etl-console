"""
Tests for BigQueryLoadAgent
"""

import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timezone
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Make sure we mock the bigquery import in case the library is not installed
# before tests run.
try:
    from agents.bigquery_load_agent import BigQueryLoadAgent
except ImportError:
    # If the import fails because google-cloud-bigquery is not installed in the
    # host environment, we'll patch it.
    sys.modules['google.cloud'] = MagicMock()
    sys.modules['google.cloud.bigquery'] = MagicMock()
    sys.modules['google.oauth2'] = MagicMock()
    from agents.bigquery_load_agent import BigQueryLoadAgent

from agents.config import PipelineConfig


@pytest.fixture
def config():
    cfg = PipelineConfig()
    cfg.load_target = "bigquery"
    cfg.bq.project_id = "test-project"
    cfg.bq.dataset = "test_dataset"
    return cfg


@pytest.fixture
def agent(config):
    return BigQueryLoadAgent(config)


def _quality_result(rows, quarantined=None):
    return {
        "status": "success",
        "data": rows,
        "rows": len(rows),
        "quarantined": quarantined or [],
        "quarantined_count": len(quarantined) if quarantined else 0,
    }


class TestBigQueryLoadAgent:

    @patch("agents.bigquery_load_agent.bigquery.Client")
    def test_skips_on_upstream_failure(self, mock_client_class, agent):
        result = agent.run({"status": "error", "data": [], "rows": 0})
        assert result["status"] == "skipped"

    @patch("agents.bigquery_load_agent.bigquery.Client")
    def test_skips_on_empty_data(self, mock_client_class, agent):
        result = agent.run(_quality_result([]))
        assert result["status"] == "skipped"
        assert result["rows_loaded"] == 0

    @patch("agents.bigquery_load_agent.bigquery.Client")
    def test_successful_load(self, mock_client_class, agent):
        mock_client = MagicMock()
        mock_client.project = "test-project"
        # insert_rows_json returns [] (no errors)
        mock_client.insert_rows_json.return_value = []
        mock_client_class.return_value = mock_client

        records = [
            {"order_id": 1, "customer_id": 101, "product_id": 5,
             "quantity": 1, "amount": 99.99, "event_type": "order_placed",
             "event_timestamp": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        ]
        quarantined = [
            {"order_id": 2, "customer_id": 102, "product_id": 6,
             "quantity": 1, "amount": 0.0, "event_type": "order_placed",
             "event_timestamp": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
             "error_message": "Amount must be > 0"}
        ]
        
        result = agent.run(_quality_result(records, quarantined), pipeline_start_time=datetime.now(timezone.utc))

        assert result["status"] == "success"
        assert result["rows_loaded"] == 1
        
        # Verify it called insert_rows_json 4 times:
        # 1. order_events
        # 2. quarantine_events
        # 3. pipeline_execution
        # 4. quality_report
        assert mock_client.insert_rows_json.call_count == 4

        # Check call arguments
        calls = mock_client.insert_rows_json.call_args_list
        tables = [c[0][0] for c in calls]
        assert "test-project.test_dataset.order_events" in tables
        assert "test-project.test_dataset.quarantine_events" in tables
        assert "test-project.test_dataset.pipeline_execution" in tables
        assert "test-project.test_dataset.quality_report" in tables

    @patch("agents.bigquery_load_agent.bigquery.Client")
    def test_bq_error_returns_error_status(self, mock_client_class, agent):
        mock_client = MagicMock()
        mock_client.project = "test-project"
        # Return insertion errors
        mock_client.insert_rows_json.return_value = [{"errors": [{"message": "Insertion failed"}]}]
        mock_client_class.return_value = mock_client

        records = [{"order_id": 1, "customer_id": 101, "product_id": 5, "quantity": 1, "amount": 99.99, "event_type": "order_placed"}]
        result = agent.run(_quality_result(records))

        assert result["status"] == "error"
        assert "Failed to insert order_events" in result["error_message"]

    @patch("agents.bigquery_load_agent.bigquery.Client")
    def test_bq_exception_returns_error_status(self, mock_client_class, agent):
        mock_client = MagicMock()
        mock_client.project = "test-project"
        mock_client.insert_rows_json.side_effect = Exception("BigQuery timeout")
        mock_client_class.return_value = mock_client

        records = [{"order_id": 1, "customer_id": 101, "product_id": 5, "quantity": 1, "amount": 99.99, "event_type": "order_placed"}]
        result = agent.run(_quality_result(records))

        assert result["status"] == "error"
        assert "BigQuery timeout" in result["error_message"]

    def test_result_structure(self, agent):
        r = agent._result("success", 5, None, 123.0)
        assert r["status"] == "success"
        assert r["rows_loaded"] == 5
        assert r["agent"] == "BigQueryLoadAgent"
        assert r["duration_ms"] == 123.0
