"""
Tests for PostgresLoadAgent
"""

import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timezone
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.postgres_load_agent import PostgresLoadAgent
from agents.config import PipelineConfig


@pytest.fixture
def agent():
    return PostgresLoadAgent(PipelineConfig())


def _quality_result(rows):
    return {
        "status": "success",
        "data": rows,
        "rows": len(rows),
        "quarantined": [],
        "quarantined_count": 0,
    }


def _mock_conn():
    """Create a mock psycopg2 connection + cursor."""
    mock_cursor = MagicMock()
    mock_cursor.__enter__ = lambda s: mock_cursor
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_cursor.rowcount = -1

    mock_conn = MagicMock()
    mock_conn.closed = False
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor


class TestPostgresLoadAgent:

    def test_skips_on_upstream_failure(self, agent):
        result = agent.run({"status": "error", "data": [], "rows": 0})
        assert result["status"] == "skipped"

    def test_skips_on_empty_data(self, agent):
        result = agent.run(_quality_result([]))
        assert result["status"] == "skipped"
        assert result["rows_loaded"] == 0

    def test_successful_load(self, agent):
        conn, cursor = _mock_conn()
        agent._conn = conn

        records = [
            {"order_id": 1, "customer_id": 101, "product_id": 5,
             "quantity": 1, "amount": 99.99, "event_type": "order_placed",
             "event_timestamp": "2024-01-01T00:00:00"},
        ]
        result = agent.run(_quality_result(records), pipeline_start_time=datetime.now(timezone.utc))

        assert result["status"] == "success"
        assert cursor.executemany.called
        assert cursor.execute.called   # pipeline_execution log
        conn.commit.assert_called_once()

    def test_db_error_returns_error_status(self, agent):
        conn, cursor = _mock_conn()
        cursor.executemany.side_effect = Exception("DB connection lost")
        agent._conn = conn

        records = [{"order_id": 1, "customer_id": 1, "amount": 10.0}]
        result = agent.run(_quality_result(records))

        assert result["status"] == "error"
        assert "DB connection lost" in result["error_message"]

    def test_result_structure(self, agent):
        r = agent._result("success", 5, None, 0.123)
        assert r["status"] == "success"
        assert r["rows_loaded"] == 5
        assert r["agent"] == "PostgresLoadAgent"
        assert r["duration_ms"] == 123.0
