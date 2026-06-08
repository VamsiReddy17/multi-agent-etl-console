"""
Tests for KafkaIngestionAgent
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.kafka_ingestion_agent import KafkaIngestionAgent
from agents.config import PipelineConfig


@pytest.fixture
def config():
    cfg = PipelineConfig()
    cfg.kafka.broker = "localhost:9092"
    cfg.kafka.batch_size = 10
    cfg.kafka.poll_timeout_ms = 100
    return cfg


@pytest.fixture
def agent(config):
    return KafkaIngestionAgent(config)


class TestKafkaIngestionAgent:

    def test_result_structure(self, agent):
        """Result dict has all required keys."""
        result = agent._result("success", [{"a": 1}], [], None, 0.01)
        assert result["status"] == "success"
        assert result["rows"] == 1
        assert result["agent"] == "KafkaIngestionAgent"
        assert "duration_ms" in result
        assert "errors" in result

    def test_poll_batch_valid_json(self, agent):
        """Valid JSON messages are parsed correctly."""
        raw = MagicMock()
        raw.value = b'{"order_id": 1, "amount": 99.99}'
        raw.topic = "orders"
        raw.partition = 0
        raw.offset = 42

        messages, errors = agent._poll_batch([raw])
        assert len(messages) == 1
        assert messages[0]["order_id"] == 1
        assert messages[0]["_topic"] == "orders"
        assert messages[0]["_offset"] == 42
        assert errors == []

    def test_poll_batch_bad_json_skipped(self, agent):
        """Bad JSON is skipped and logged as an error."""
        raw = MagicMock()
        raw.value = b"NOT JSON {"
        raw.topic = "orders"
        raw.partition = 0
        raw.offset = 99

        messages, errors = agent._poll_batch([raw])
        assert messages == []
        assert len(errors) == 1
        assert "offset=99" in errors[0]

    def test_poll_batch_respects_batch_size(self, agent):
        """Batch size limit is respected."""
        agent.config.kafka.batch_size = 3

        raws = []
        for i in range(10):
            raw = MagicMock()
            raw.value = f'{{"order_id": {i}}}'.encode()
            raw.topic = "orders"
            raw.partition = 0
            raw.offset = i
            raws.append(raw)

        messages, errors = agent._poll_batch(raws)
        assert len(messages) == 3

    def test_run_returns_error_on_connection_failure(self, agent):
        """Connection errors are caught and returned as error status."""
        with patch.object(agent, "_get_consumer", side_effect=RuntimeError("Kafka down")):
            result = agent.run(topics=["orders"])
        assert result["status"] == "error"
        assert "Kafka down" in result["error_message"]

    def test_run_returns_no_messages(self, agent):
        """Empty poll returns success with 0 rows."""
        with patch.object(agent, "_get_consumer", return_value=[]):
            result = agent.run(topics=["orders"])
        assert result["status"] == "success"
        assert result["rows"] == 0
