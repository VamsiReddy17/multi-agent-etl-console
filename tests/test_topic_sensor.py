"""
Tests for KafkaTopicSensor
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "airflow", "plugins"))

from kafka_topic_sensor import KafkaTopicSensor
from kafka import TopicPartition


class TestKafkaTopicSensor:

    @patch("kafka_topic_sensor.KafkaConsumer")
    def test_poke_returns_true_when_lag_exists(self, mock_consumer_class):
        """poke() returns True if there is consumer lag on monitored partitions."""
        sensor = KafkaTopicSensor(task_id="test_sensor", topics=["orders"])
        
        mock_consumer = MagicMock()
        mock_consumer_class.return_value = mock_consumer
        
        # Mock partition details
        mock_consumer.partitions_for_topic.return_value = [0, 1]
        
        # Mock offsets
        tp0 = TopicPartition("orders", 0)
        tp1 = TopicPartition("orders", 1)
        mock_consumer.end_offsets.return_value = {tp0: 100, tp1: 150}
        
        # Mock positions (current offsets)
        mock_consumer.position.side_effect = lambda tp: 90 if tp == tp0 else 150

        # tp0 lag = 100 - 90 = 10. tp1 lag = 150 - 150 = 0. Total lag = 10.
        result = sensor.poke(context={})
        assert result is True
        mock_consumer.close.assert_called_once()

    @patch("kafka_topic_sensor.KafkaConsumer")
    def test_poke_returns_false_when_no_lag(self, mock_consumer_class):
        """poke() returns False if consumer has caught up (no lag)."""
        sensor = KafkaTopicSensor(task_id="test_sensor", topics=["orders"])
        
        mock_consumer = MagicMock()
        mock_consumer_class.return_value = mock_consumer
        mock_consumer.partitions_for_topic.return_value = [0]
        
        tp = TopicPartition("orders", 0)
        mock_consumer.end_offsets.return_value = {tp: 100}
        mock_consumer.position.return_value = 100

        result = sensor.poke(context={})
        assert result is False

    @patch("kafka_topic_sensor.KafkaConsumer")
    def test_poke_returns_false_on_connection_error(self, mock_consumer_class):
        """poke() returns False if Kafka throws an error."""
        sensor = KafkaTopicSensor(task_id="test_sensor", topics=["orders"])
        mock_consumer_class.side_effect = Exception("Kafka broker offline")

        result = sensor.poke(context={})
        assert result is False
