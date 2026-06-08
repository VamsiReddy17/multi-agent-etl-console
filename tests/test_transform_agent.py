"""
Tests for TransformAgent
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.transform_agent import TransformAgent
from agents.config import PipelineConfig


@pytest.fixture
def agent():
    return TransformAgent(PipelineConfig())


def _ingest_result(rows):
    return {"status": "success", "data": rows, "rows": len(rows)}


class TestTransformAgent:

    def test_basic_transform(self, agent):
        """Standard record is enriched correctly."""
        result = agent.run(_ingest_result([{
            "order_id": "1",
            "customer_id": "101",
            "product_id": "5",
            "quantity": "2",
            "amount": "49.99",
            "event_type": "ORDER_PLACED",
        }]))
        assert result["status"] == "success"
        assert result["rows"] == 1
        rec = result["data"][0]
        assert rec["order_id"] == 1
        assert rec["customer_id"] == 101
        assert rec["quantity"] == 2
        assert rec["amount"] == 49.99
        assert rec["event_type"] == "order_placed"   # lowercased
        assert rec["total_amount"] == 99.98
        assert "processed_at" in rec

    def test_total_amount_calculated(self, agent):
        """total_amount = quantity * unit_price when not provided."""
        result = agent.run(_ingest_result([{
            "order_id": 2, "customer_id": 1,
            "quantity": "3", "amount": "10.00",
        }]))
        assert result["data"][0]["total_amount"] == 30.0

    def test_total_amount_not_overwritten(self, agent):
        """Existing total_amount is preserved."""
        result = agent.run(_ingest_result([{
            "order_id": 3, "customer_id": 1,
            "quantity": "1", "amount": "10.00",
            "total_amount": 999.0,
        }]))
        assert result["data"][0]["total_amount"] == 999.0

    def test_pipeline_metadata_added(self, agent):
        """Pipeline name and version are injected."""
        result = agent.run(_ingest_result([{"order_id": 4, "customer_id": 1, "amount": "5"}]))
        rec = result["data"][0]
        assert "_pipeline_name" in rec
        assert "_pipeline_version" in rec

    def test_skips_on_upstream_failure(self, agent):
        """Skips gracefully if upstream status is not success."""
        result = agent.run({"status": "error", "data": [], "rows": 0})
        assert result["status"] == "skipped"
        assert result["rows"] == 0

    def test_bad_amount_defaults_to_zero(self, agent):
        """Non-numeric amount falls back to 0.0."""
        result = agent.run(_ingest_result([{
            "order_id": 5, "customer_id": 1, "amount": "NOT_A_NUMBER",
        }]))
        assert result["data"][0]["amount"] == 0.0

    def test_multiple_records(self, agent):
        """All records in a batch are transformed."""
        rows = [{"order_id": i, "customer_id": 1, "amount": str(i * 10)} for i in range(1, 6)]
        result = agent.run(_ingest_result(rows))
        assert result["rows"] == 5
