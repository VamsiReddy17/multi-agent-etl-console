"""
Tests for DLQ Retry Logic (scripts/retry_dlq.py)
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.retry_dlq import extract_retry_count, write_to_permanent_failures


class TestDLQRetry:

    def test_extract_retry_count_default(self):
        """Returns 1 if msg.headers is empty or none."""
        mock_msg = MagicMock()
        mock_msg.headers = None
        assert extract_retry_count(mock_msg) == 1

        mock_msg.headers = []
        assert extract_retry_count(mock_msg) == 1

    def test_extract_retry_count_from_header(self):
        """Successfully parses retry_count from headers."""
        mock_msg = MagicMock()
        mock_msg.headers = [("retry_count", b"3"), ("other_header", b"abc")]
        assert extract_retry_count(mock_msg) == 3

    def test_extract_retry_count_invalid_header(self):
        """Falls back to 1 if retry_count value is invalid integer."""
        mock_msg = MagicMock()
        mock_msg.headers = [("retry_count", b"invalid_number")]
        assert extract_retry_count(mock_msg) == 1

    @patch("psycopg2.connect")
    def test_write_to_permanent_failures(self, mock_connect):
        """Calls execution block to insert permanent failure record into database."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_connect.return_value = mock_conn

        mock_config = MagicMock()
        mock_config.db.dsn = {}
        
        record = {
            "order_id": 123,
            "customer_id": 1,
            "product_id": 2,
            "quantity": 3,
            "amount": 49.99,
            "event_type": "order_placed",
            "event_timestamp": "2026-06-17T12:00:00Z"
        }

        write_to_permanent_failures(mock_config, record, 3, "Amount must be > 0")

        assert mock_connect.call_count == 1
        assert mock_cur.execute.call_count == 1
        assert mock_conn.commit.call_count == 1
        assert mock_conn.close.call_count == 1
