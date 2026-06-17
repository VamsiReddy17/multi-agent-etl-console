"""
Tests for DeadLetterAgent
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.dead_letter_agent import DeadLetterAgent
from agents.config import PipelineConfig


@pytest.fixture
def config():
    cfg = PipelineConfig()
    cfg.kafka.broker = "localhost:9092"
    return cfg


@pytest.fixture
def agent(config):
    return DeadLetterAgent(config)


class TestDeadLetterAgent:

    def test_result_structure(self, agent):
        """Result dict has all standard keys."""
        result = agent._result("success", 2, None, 0.01)
        assert result["status"] == "success"
        assert result["rows_sent"] == 2
        assert result["rows"] == 2
        assert result["agent"] == "DeadLetterAgent"
        assert "duration_ms" in result
        assert "errors" in result

    def test_run_skips_upstream_failure(self, agent):
        """Skips run if upstream status is skipped/error."""
        result = agent.run({"status": "skipped", "quarantined": []})
        assert result["status"] == "skipped"
        assert result["rows_sent"] == 0

    def test_run_with_no_quarantined_records(self, agent):
        """Succeeds immediately with 0 rows sent when no quarantined records exist."""
        result = agent.run({"status": "success", "quarantined": []})
        assert result["status"] == "success"
        assert result["rows_sent"] == 0

    def test_run_produces_to_dlq(self, agent):
        """Successfully routes quarantined records to Kafka DLQ."""
        mock_producer = MagicMock()
        quarantined_records = [
            {"order_id": 1, "error_message": "Missing amount"},
            {"order_id": 2, "error_message": "Negative quantity"}
        ]

        with patch.object(agent, "_get_producer", return_value=mock_producer):
            result = agent.run({"status": "success", "quarantined": quarantined_records})

        assert result["status"] == "success"
        assert result["rows_sent"] == 2
        assert mock_producer.send.call_count == 2
        mock_producer.send.assert_any_call("dead_letter", quarantined_records[0])
        mock_producer.send.assert_any_call("dead_letter", quarantined_records[1])
        assert mock_producer.flush.call_count == 1

    def test_run_returns_error_on_failure(self, agent):
        """Catches exception and returns error status."""
        with patch.object(agent, "_get_producer", side_effect=Exception("Kafka connection dropped")):
            result = agent.run({"status": "success", "quarantined": [{"order_id": 1}]})
        assert result["status"] == "error"
        assert result["rows_sent"] == 0
        assert "Kafka connection dropped" in result["error_message"]
