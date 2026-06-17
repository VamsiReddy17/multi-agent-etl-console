"""
Tests for FastAPI REST API endpoints
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import HTTPException

from api.server import health, trigger_run, get_status


class TestETLAPI:

    def test_health_endpoint(self):
        data = health()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    @patch("api.server.StreamingETL")
    def test_pipeline_run_endpoint_success(self, mock_etl_class):
        mock_etl = MagicMock()
        mock_etl.run_once.return_value = {
            "status": "success",
            "total_ms": 150.0,
            "stages": []
        }
        mock_etl_class.return_value = mock_etl

        data = trigger_run()
        assert data["status"] == "success"
        assert data["total_ms"] == 150.0
        mock_etl.run_once.assert_called_once()

    @patch("api.server.StreamingETL")
    def test_pipeline_run_endpoint_failure(self, mock_etl_class):
        mock_etl = MagicMock()
        mock_etl.run_once.side_effect = Exception("Kafka Broker Down")
        mock_etl_class.return_value = mock_etl

        with pytest.raises(HTTPException) as exc_info:
            trigger_run()
        assert exc_info.value.status_code == 500
        assert "Kafka Broker Down" in exc_info.value.detail

    @patch("psycopg2.connect")
    @patch("api.server.PipelineConfig")
    def test_pipeline_status_postgres_success(self, mock_config_class, mock_connect):
        # Set config target to postgres
        mock_config = MagicMock()
        mock_config.load_target = "postgres"
        mock_config.db.dsn = {}
        mock_config_class.return_value = mock_config

        # Mock Postgres connection
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (
            "streaming-etl",
            datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
            "success",
            100,
            None
        )
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        data = get_status()
        assert data["pipeline_name"] == "streaming-etl"
        assert data["status"] == "success"
        assert data["rows_processed"] == 100

    @patch("psycopg2.connect")
    @patch("api.server.PipelineConfig")
    def test_pipeline_status_postgres_no_data(self, mock_config_class, mock_connect):
        mock_config = MagicMock()
        mock_config.load_target = "postgres"
        mock_config_class.return_value = mock_config

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        data = get_status()
        assert "No pipeline executions found" in data["message"]

    @patch("google.cloud.bigquery.Client")
    @patch("api.server.PipelineConfig")
    def test_pipeline_status_bigquery_success(self, mock_config_class, mock_bq_client_class):
        # Set config target to bigquery
        mock_config = MagicMock()
        mock_config.load_target = "bigquery"
        mock_config.bq.project_id = "test-project"
        mock_config.bq.dataset = "test_dataset"
        mock_config_class.return_value = mock_config

        # Mock BigQuery Client & Results
        mock_row = MagicMock()
        mock_row.get.side_effect = lambda key: {
            "pipeline_name": "streaming-etl",
            "start_time": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "end_time": datetime(2024, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
            "status": "success",
            "rows_processed": 250,
            "error_message": None
        }.get(key)

        mock_results = [mock_row]
        mock_query_job = MagicMock()
        mock_query_job.result.return_value = mock_results
        
        mock_bq_client = MagicMock()
        mock_bq_client.project = "test-project"
        mock_bq_client.query.return_value = mock_query_job
        mock_bq_client_class.return_value = mock_bq_client

        data = get_status()
        assert data["pipeline_name"] == "streaming-etl"
        assert data["status"] == "success"
        assert data["rows_processed"] == 250
