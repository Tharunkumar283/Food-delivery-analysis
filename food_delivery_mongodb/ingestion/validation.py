"""
ingestion/validation.py
Row-level validation. Returns valid records and a list of rejection reasons.
"""
import logging
from datetime import datetime, timezone
import pandas as pd
from config.settings import settings

logger = logging.getLogger(__name__)

_MIN_DATE = datetime(2015, 1, 1, tzinfo=timezone.utc)
_MAX_DATE = datetime(2030, 12, 31, tzinfo=timezone.utc)


def _to_utc(dt) -> datetime | None:
    if dt is None or (isinstance(dt, float)):
        return None
    if isinstance(dt, pd.Timestamp):
        dt = dt.to_pydatetime()
    if isinstance(dt, datetime) and dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def validate_record(rec: dict) -> list[str]:
    """
    Validate a single order record.
    Returns a list of error strings (empty list = valid).
    """
    errors: list[str] = []

    # ── Required fields ───────────────────────────────────────────────────────
    for field in settings.REQUIRED_FIELDS:
        val = rec.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            errors.append(f"Missing required field: {field}")

    if errors:  # No point continuing if required fields are absent
        return errors

    # ── order_id ──────────────────────────────────────────────────────────────
    order_id = str(rec.get("order_id", "")).strip()
    if not order_id:
        errors.append("order_id is empty")

    # ── order_date ────────────────────────────────────────────────────────────
    raw_date = rec.get("order_date")
    if raw_date is None:
        errors.append("order_date is missing or invalid")
    else:
        dt = _to_utc(raw_date)
        if dt is None:
            errors.append("order_date could not be parsed")
        elif not (_MIN_DATE <= dt <= _MAX_DATE):
            errors.append(f"order_date {dt.date()} is out of expected range")

    # ── total_amount ──────────────────────────────────────────────────────────
    total = rec.get("total_amount")
    if total is None:
        errors.append("total_amount is missing")
    elif not isinstance(total, (int, float)):
        errors.append("total_amount must be numeric")
    elif total < 0:
        errors.append(f"total_amount is negative ({total})")

    # ── quantity (optional but must be positive if present) ───────────────────
    qty = rec.get("quantity")
    if qty is not None and (not isinstance(qty, (int, float)) or qty <= 0):
        errors.append(f"quantity must be a positive number, got {qty}")

    # ── item_price (optional) ─────────────────────────────────────────────────
    price = rec.get("item_price")
    if price is not None and (not isinstance(price, (int, float)) or price < 0):
        errors.append(f"item_price must be non-negative, got {price}")

    # ── delivery_time_minutes (optional) ──────────────────────────────────────
    dt_min = rec.get("delivery_time_minutes")
    if dt_min is not None:
        if not isinstance(dt_min, (int, float)) or dt_min < 0 or dt_min > 600:
            errors.append(f"delivery_time_minutes out of range (0-600): {dt_min}")

    # ── customer_rating (optional) ────────────────────────────────────────────
    rating = rec.get("customer_rating")
    if rating is not None:
        if not isinstance(rating, (int, float)) or not (0 <= rating <= 5):
            errors.append(f"customer_rating must be 0-5, got {rating}")

    # ── order_status (optional) ───────────────────────────────────────────────
    status = rec.get("order_status")
    if status is not None:
        if str(status).lower() not in settings.VALID_ORDER_STATUSES:
            errors.append(f"Unknown order_status: {status!r}")

    return errors


def validate_batch(records: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Validate a batch of records.
    Returns (valid_records, rejected_records).
    Each rejected record has an extra "_rejection_reasons" key.
    """
    valid, rejected = [], []
    for rec in records:
        errs = validate_record(rec)
        if errs:
            rec["_rejection_reasons"] = errs
            rejected.append(rec)
        else:
            valid.append(rec)
    return valid, rejected
