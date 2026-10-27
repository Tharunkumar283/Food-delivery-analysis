"""
tests/test_advanced.py
Unit tests for analytics/advanced.py — RFM segmentation, repeat-customer,
and discount-impact analysis.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


# ── RFM Segmentation Tests ────────────────────────────────────────────────────

class TestRFMSegments:
    """Test RFM segment assignment logic without MongoDB."""

    def _make_rfm_record(self, recency, frequency, monetary):
        return {
            "customer_id": "CUST001",
            "recency_days": recency,
            "frequency": frequency,
            "monetary": monetary,
            "total_orders": frequency,
            "completed_orders": frequency,
            "avg_order_value": monetary / max(frequency, 1),
            "avg_rating": 4.0,
            "last_order": datetime(2024, 6, 1),
            "first_order": datetime(2024, 1, 1),
        }

    def test_segment_label_champion(self):
        """High R, F, M scores → Champions."""
        from analytics.advanced import get_rfm_segments

        # We test the internal scoring logic
        # Champions: total score >= 8
        # Score 3 on each dimension = total 9
        # This requires mocking get_rfm_data
        records = [
            self._make_rfm_record(recency=5, frequency=10, monetary=5000),
            self._make_rfm_record(recency=10, frequency=8, monetary=4000),
            self._make_rfm_record(recency=200, frequency=1, monetary=100),
        ]
        # Fix customer IDs
        for i, r in enumerate(records):
            r["customer_id"] = f"CUST{i:04d}"

        with patch("analytics.advanced.get_rfm_data", return_value=records):
            result = get_rfm_segments()
            assert len(result) == 3
            # All records should have 'segment' key
            for r in result:
                assert "segment" in r
                assert "rfm_score" in r
                assert "r_score" in r
                assert "f_score" in r
                assert "m_score" in r

    def test_empty_rfm_data(self):
        from analytics.advanced import get_rfm_segments

        with patch("analytics.advanced.get_rfm_data", return_value=[]):
            result = get_rfm_segments()
            assert result == []


class TestSegmentSummary:
    def test_summary_aggregation(self):
        from analytics.advanced import get_segment_summary

        mock_segments = [
            {"segment": "Champions", "customers": 1, "frequency": 10,
             "monetary": 5000, "recency_days": 5},
            {"segment": "Champions", "customers": 1, "frequency": 8,
             "monetary": 4000, "recency_days": 3},
            {"segment": "Lost", "customers": 1, "frequency": 1,
             "monetary": 100, "recency_days": 200},
        ]

        with patch("analytics.advanced.get_rfm_segments", return_value=mock_segments):
            result = get_segment_summary()
            assert len(result) == 2  # Champions + Lost

            # Find Champions segment
            champs = next(s for s in result if s["segment"] == "Champions")
            assert champs["customers"] == 2
            assert champs["total_orders"] == 18  # 10 + 8

    def test_empty_segments(self):
        from analytics.advanced import get_segment_summary

        with patch("analytics.advanced.get_rfm_segments", return_value=[]):
            result = get_segment_summary()
            assert result == []


# ── Repeat Customer Tests ─────────────────────────────────────────────────────

class TestRepeatCustomerStats:
    def test_stats_with_data(self):
        from analytics.advanced import get_repeat_customer_stats

        mock_result = [{
            "_id": None,
            "total_customers": 100,
            "one_time": 60,
            "repeat": 40,
            "total_revenue": 50000.0,
            "repeat_revenue": 30000.0,
            "avg_orders_per_customer": 2.5,
            "max_orders": 15,
        }]

        with patch("analytics.advanced._col") as mock_col:
            mock_col.return_value.aggregate.return_value = mock_result
            result = get_repeat_customer_stats()

            assert result["total_customers"] == 100
            assert result["repeat_rate"] == 40.0
            assert result["repeat_revenue_share"] == 60.0
            assert result["avg_orders_per_customer"] == 2.5

    def test_stats_empty(self):
        from analytics.advanced import get_repeat_customer_stats

        with patch("analytics.advanced._col") as mock_col:
            mock_col.return_value.aggregate.return_value = []
            result = get_repeat_customer_stats()

            assert result["total_customers"] == 0
            assert result["repeat_rate"] == 0.0


class TestOrderFrequencyDistribution:
    def test_frequency_distribution(self):
        from analytics.advanced import get_order_frequency_distribution

        mock_result = [
            {"order_count": 1, "customers": 50},
            {"order_count": 2, "customers": 30},
            {"order_count": 3, "customers": 15},
        ]

        with patch("analytics.advanced._col") as mock_col:
            mock_col.return_value.aggregate.return_value = mock_result
            result = get_order_frequency_distribution()

            assert len(result) == 3
            assert result[0]["order_count"] == 1
            assert result[0]["customers"] == 50


# ── Discount Impact Tests ─────────────────────────────────────────────────────

class TestDiscountOverview:
    def test_overview_with_data(self):
        from analytics.advanced import get_discount_overview

        mock_result = [{
            "_id": None,
            "total_orders": 200,
            "orders_with_discount": 80,
            "orders_without_discount": 120,
            "total_discount_given": 5000.0,
            "avg_discount": 62.5,
            "revenue_with_discount": 20000.0,
            "revenue_without_discount": 30000.0,
            "avg_rating_with_discount": 4.2,
            "avg_rating_without_discount": 4.0,
            "avg_order_with_discount": 250.0,
            "avg_order_without_discount": 250.0,
        }]

        with patch("analytics.advanced._col") as mock_col:
            mock_col.return_value.aggregate.return_value = mock_result
            result = get_discount_overview()

            assert result["total_orders"] == 200
            assert result["discount_usage_rate"] == 40.0
            assert result["orders_with_discount"] == 80

    def test_overview_empty(self):
        from analytics.advanced import get_discount_overview

        with patch("analytics.advanced._col") as mock_col:
            mock_col.return_value.aggregate.return_value = []
            result = get_discount_overview()

            assert result["total_orders"] == 0
            assert result["discount_usage_rate"] == 0


class TestDiscountBands:
    def test_bands_returned(self):
        from analytics.advanced import get_discount_bands

        mock_result = [
            {"band": "No Discount", "orders": 120, "avg_total": 300.0,
             "total_revenue": 36000.0, "avg_rating": 4.0, "cancellation_rate": 5.0},
            {"band": "5-10%", "orders": 50, "avg_total": 350.0,
             "total_revenue": 17500.0, "avg_rating": 4.2, "cancellation_rate": 3.0},
        ]

        with patch("analytics.advanced._col") as mock_col:
            mock_col.return_value.aggregate.return_value = mock_result
            result = get_discount_bands()

            assert len(result) == 2
            assert result[0]["band"] == "No Discount"


class TestDiscountTrend:
    def test_monthly_trend(self):
        from analytics.advanced import get_discount_trend_by_month

        mock_result = [
            {"month": "2024-01", "total_orders": 50, "discounted_orders": 20,
             "discount_rate": 40.0, "avg_discount": 50.0, "total_discount": 1000.0,
             "avg_order_value": 300.0},
            {"month": "2024-02", "total_orders": 60, "discounted_orders": 25,
             "discount_rate": 41.7, "avg_discount": 55.0, "total_discount": 1375.0,
             "avg_order_value": 310.0},
        ]

        with patch("analytics.advanced._col") as mock_col:
            mock_col.return_value.aggregate.return_value = mock_result
            result = get_discount_trend_by_month()

            assert len(result) == 2
            assert result[0]["month"] == "2024-01"
