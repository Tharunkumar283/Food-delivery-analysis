"""
analytics/metrics.py
High-level metric helpers that call aggregations and format results.
"""
from __future__ import annotations
from datetime import datetime
from analytics.aggregations import (
    get_overview_kpis,
    get_revenue_by_day,
    get_revenue_by_month,
)


def realized_revenue(
    start: datetime | None = None,
    end: datetime | None = None,
    city: str | None = None,
    restaurant: str | None = None,
) -> float:
    """
    Realized revenue = sum of total_amount for Completed / Delivered orders.
    Cancelled orders are excluded.
    """
    kpis = get_overview_kpis(start=start, end=end, city=city, restaurant=restaurant)
    return kpis.get("total_revenue", 0.0)


def cancellation_rate(
    start: datetime | None = None,
    end: datetime | None = None,
) -> float:
    kpis = get_overview_kpis(start=start, end=end)
    return kpis.get("cancellation_rate", 0.0)


def average_order_value(
    start: datetime | None = None,
    end: datetime | None = None,
) -> float:
    kpis = get_overview_kpis(start=start, end=end)
    return kpis.get("avg_order_value", 0.0)


def daily_revenue_series(
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[dict]:
    return get_revenue_by_day(start=start, end=end)


def monthly_revenue_series(
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[dict]:
    return get_revenue_by_month(start=start, end=end)
