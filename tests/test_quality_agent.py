"""
Tests for QualityAgent
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.quality_agent import QualityAgent
from agents.config import PipelineConfig


@pytest.fixture
def agent():
    return QualityAgent(PipelineConfig())


def _transform_result(rows):
    return {"status": "success", "data": rows, "rows": len(rows)}


def _good_record(order_id=1):
    return {
        "order_id": order_id,
        "customer_id": 101,
        "product_id": 5,
        "quantity": 2,
        "amount": 49.99,
        "event_type": "order_placed",
    }


class TestQualityAgent:

    def test_valid_record_passes(self, agent):
        result = agent.run(_transform_result([_good_record()]))
        assert result["status"] == "success"
        assert result["rows"] == 1
        assert result["quarantined_count"] == 0

    def test_missing_required_field_quarantined(self, agent):
        bad = {"customer_id": 1, "amount": 10.0}  # missing order_id
        result = agent.run(_transform_result([bad]))
        assert result["rows"] == 0
        assert result["quarantined_count"] == 1

    def test_zero_amount_quarantined(self, agent):
        bad = _good_record()
        bad["amount"] = 0
        result = agent.run(_transform_result([bad]))
        assert result["quarantined_count"] == 1

    def test_negative_amount_quarantined(self, agent):
        bad = _good_record()
        bad["amount"] = -5.0
        result = agent.run(_transform_result([bad]))
        assert result["quarantined_count"] == 1

    def test_duplicate_order_id_quarantined(self, agent):
        records = [_good_record(order_id=42), _good_record(order_id=42)]
        result = agent.run(_transform_result(records))
        assert result["rows"] == 1
        assert result["quarantined_count"] == 1

    def test_unknown_event_type_quarantined(self, agent):
        bad = _good_record()
        bad["event_type"] = "totally_unknown_event"
        result = agent.run(_transform_result([bad]))
        assert result["quarantined_count"] == 1

    def test_mixed_valid_and_invalid(self, agent):
        records = [
            _good_record(order_id=1),
            {"customer_id": 1, "amount": -1},   # bad
            _good_record(order_id=3),
        ]
        result = agent.run(_transform_result(records))
        assert result["rows"] == 2
        assert result["quarantined_count"] == 1

    def test_skips_on_upstream_failure(self, agent):
        result = agent.run({"status": "error", "data": [], "rows": 0})
        assert result["status"] == "skipped"

    def test_empty_batch_returns_success(self, agent):
        result = agent.run(_transform_result([]))
        assert result["status"] == "success"
        assert result["rows"] == 0
        assert result["quarantined_count"] == 0
