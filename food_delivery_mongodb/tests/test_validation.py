"""
tests/test_validation.py
Unit tests for ingestion/validation.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime
from ingestion.validation import validate_record, validate_batch


def _good_record(**overrides):
    base = {
        "order_id": "ORD001",
        "order_date": datetime(2024, 3, 15, 12, 0, 0),
        "restaurant_name": "Test Restaurant",
        "total_amount": 250.0,
        "order_status": "Completed",
        "quantity": 2,
        "item_price": 120.0,
        "customer_rating": 4.5,
        "delivery_time_minutes": 30,
    }
    base.update(overrides)
    return base


class TestValidateRecord:
    def test_valid_record_passes(self):
        assert validate_record(_good_record()) == []

    def test_missing_order_id(self):
        errs = validate_record(_good_record(order_id=None))
        assert any("order_id" in e for e in errs)

    def test_empty_order_id(self):
        errs = validate_record(_good_record(order_id=""))
        assert any("order_id" in e for e in errs)

    def test_missing_order_date(self):
        errs = validate_record(_good_record(order_date=None))
        assert any("order_date" in e for e in errs)

    def test_missing_restaurant(self):
        errs = validate_record(_good_record(restaurant_name=None))
        assert any("restaurant_name" in e for e in errs)

    def test_negative_total(self):
        errs = validate_record(_good_record(total_amount=-10.0))
        assert any("negative" in e.lower() or "total_amount" in e for e in errs)

    def test_zero_total_allowed(self):
        # A $0 order (e.g. fully discounted) should be valid
        assert validate_record(_good_record(total_amount=0.0)) == []

    def test_invalid_quantity(self):
        errs = validate_record(_good_record(quantity=-1))
        assert any("quantity" in e for e in errs)

    def test_rating_out_of_range_high(self):
        errs = validate_record(_good_record(customer_rating=6.0))
        assert any("rating" in e for e in errs)

    def test_rating_out_of_range_low(self):
        errs = validate_record(_good_record(customer_rating=-1.0))
        assert any("rating" in e for e in errs)

    def test_valid_rating_boundary(self):
        assert validate_record(_good_record(customer_rating=0.0)) == []
        assert validate_record(_good_record(customer_rating=5.0)) == []

    def test_delivery_time_too_large(self):
        errs = validate_record(_good_record(delivery_time_minutes=700))
        assert any("delivery_time" in e for e in errs)

    def test_delivery_time_none_allowed(self):
        assert validate_record(_good_record(delivery_time_minutes=None)) == []

    def test_unknown_order_status(self):
        errs = validate_record(_good_record(order_status="UNKNOWN_STATUS"))
        assert any("status" in e.lower() for e in errs)

    def test_valid_statuses(self):
        for status in ["Completed", "Delivered", "Cancelled", "Pending"]:
            assert validate_record(_good_record(order_status=status)) == []


class TestValidateBatch:
    def test_batch_separates_valid_and_invalid(self):
        records = [
            _good_record(order_id="ORD001"),
            _good_record(order_id=None),  # invalid
            _good_record(order_id="ORD003", customer_rating=99),  # invalid
        ]
        valid, rejected = validate_batch(records)
        assert len(valid) == 1
        assert len(rejected) == 2

    def test_rejected_has_reasons(self):
        _, rejected = validate_batch([_good_record(order_id=None)])
        assert "_rejection_reasons" in rejected[0]
        assert isinstance(rejected[0]["_rejection_reasons"], list)

    def test_empty_batch(self):
        valid, rejected = validate_batch([])
        assert valid == []
        assert rejected == []
