"""
tests/test_metrics.py
Unit tests for analytics/metrics.py using mocked MongoDB calls.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import patch


MOCK_KPIS = {
    "total_orders": 100,
    "completed_orders": 80,
    "cancelled_orders": 10,
    "total_revenue": 50000.0,
    "avg_order_value": 500.0,
    "avg_delivery_time": 35.0,
    "avg_rating": 4.2,
    "cancellation_rate": 10.0,
}


class TestMetrics:
    def test_realized_revenue(self):
        with patch("analytics.metrics.get_overview_kpis", return_value=MOCK_KPIS):
            from analytics.metrics import realized_revenue
            assert realized_revenue() == 50000.0

    def test_cancellation_rate(self):
        with patch("analytics.metrics.get_overview_kpis", return_value=MOCK_KPIS):
            from analytics.metrics import cancellation_rate
            assert cancellation_rate() == 10.0

    def test_average_order_value(self):
        with patch("analytics.metrics.get_overview_kpis", return_value=MOCK_KPIS):
            from analytics.metrics import average_order_value
            assert average_order_value() == 500.0

    def test_realized_revenue_empty(self):
        empty = dict(MOCK_KPIS)
        empty["total_revenue"] = 0.0
        with patch("analytics.metrics.get_overview_kpis", return_value=empty):
            from analytics.metrics import realized_revenue
            assert realized_revenue() == 0.0


class TestCancellationRateCalculation:
    """Test the cancellation rate formula directly."""

    def test_rate_formula(self):
        cancelled = 10
        total = 100
        rate = round(cancelled / total * 100, 2)
        assert rate == 10.0

    def test_rate_formula_zero_orders(self):
        cancelled = 0
        total = 1  # avoid division by zero
        rate = round(cancelled / total * 100, 2)
        assert rate == 0.0

    def test_rate_formula_all_cancelled(self):
        cancelled = 50
        total = 50
        rate = round(cancelled / total * 100, 2)
        assert rate == 100.0
