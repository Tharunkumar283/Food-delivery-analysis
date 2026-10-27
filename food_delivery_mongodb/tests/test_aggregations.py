"""
tests/test_aggregations.py
Tests for aggregation pipeline construction and preprocessing logic.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from ingestion.preprocessing import (
    normalise_column_names,
    apply_column_mapping,
    clean_dataframe,
    prepare_for_mongo,
)
from analytics.aggregations import _filter_match


class TestPreprocessing:
    def test_normalise_column_names(self):
        df = pd.DataFrame(columns=["Order ID", "Order-Date", "Total Amount"])
        result = normalise_column_names(df)
        assert list(result.columns) == ["order_id", "order_date", "total_amount"]

    def test_apply_column_mapping(self):
        df = pd.DataFrame({"date": ["2024-01-01"], "total": [200.0]})
        df = normalise_column_names(df)
        result = apply_column_mapping(df)
        assert "order_date" in result.columns
        assert "total_amount" in result.columns

    def test_clean_dataframe_parses_dates(self):
        df = pd.DataFrame({
            "order_id": ["ORD001"],
            "order_date": ["2024-03-15 12:00:00"],
            "restaurant_name": ["Test"],
            "total_amount": [300.0],
        })
        result = clean_dataframe(df)
        assert pd.api.types.is_datetime64_any_dtype(result["order_date"])

    def test_clean_dataframe_fills_discount(self):
        df = pd.DataFrame({
            "order_id": ["ORD001"],
            "order_date": ["2024-01-01"],
            "restaurant_name": ["Test"],
            "total_amount": [100.0],
            "discount": [None],
        })
        result = clean_dataframe(df)
        assert result["discount"].iloc[0] == 0.0

    def test_clean_dataframe_coerces_numerics(self):
        df = pd.DataFrame({
            "order_id": ["ORD001"],
            "order_date": ["2024-01-01"],
            "restaurant_name": ["Test"],
            "total_amount": ["250"],
            "quantity": ["3"],
        })
        result = clean_dataframe(df)
        assert result["total_amount"].dtype in [np.float64, np.int64, float, int]
        assert result["quantity"].dtype in [np.float64, np.int64, float, int]

    def test_prepare_for_mongo_removes_nan(self):
        df = pd.DataFrame({
            "order_id": ["ORD001"],
            "order_date": [pd.Timestamp("2024-01-01")],
            "restaurant_name": ["Test"],
            "total_amount": [100.0],
            "customer_rating": [float("nan")],
        })
        records = prepare_for_mongo(df)
        assert records[0]["customer_rating"] is None

    def test_prepare_for_mongo_converts_timestamps(self):
        df = pd.DataFrame({
            "order_id": ["ORD001"],
            "order_date": [pd.Timestamp("2024-03-15 10:00:00")],
            "restaurant_name": ["Test"],
            "total_amount": [200.0],
        })
        records = prepare_for_mongo(df)
        assert isinstance(records[0]["order_date"], datetime)


class TestFilterMatch:
    def test_empty_filter(self):
        result = _filter_match()
        assert result == {}

    def test_date_range_filter(self):
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        result = _filter_match(start=start, end=end)
        assert "order_date" in result
        assert result["order_date"]["$gte"] == start
        assert result["order_date"]["$lte"] == end

    def test_city_filter(self):
        result = _filter_match(city="Mumbai")
        assert result.get("city") == "Mumbai"

    def test_combined_filter(self):
        result = _filter_match(
            city="Delhi",
            restaurant="Test Rest",
            order_status="Completed",
        )
        assert result["city"] == "Delhi"
        assert result["restaurant_name"] == "Test Rest"
        assert result["order_status"] == "Completed"

    def test_none_values_excluded(self):
        result = _filter_match(city=None, restaurant=None)
        assert "city" not in result
        assert "restaurant_name" not in result


class TestCSVExport:
    def test_export_empty_returns_empty_bytes(self):
        from utils.export import export_summary_csv
        result = export_summary_csv([])
        assert result == b""

    def test_export_summary_contains_headers(self):
        from utils.export import export_summary_csv
        data = [{"restaurant": "Test", "revenue": 1000}]
        result = export_summary_csv(data)
        assert b"restaurant" in result
        assert b"revenue" in result
