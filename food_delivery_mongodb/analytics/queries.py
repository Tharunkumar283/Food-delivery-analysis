"""
analytics/queries.py
Thin query helpers for the Data Explorer page (paginated record fetching,
distinct-value lookups for filter dropdowns).
"""
from __future__ import annotations
from datetime import datetime

from database.repositories import (
    fetch_orders_page,
    count_orders,
    distinct_values,
    fetch_import_logs,
)
from analytics.aggregations import _filter_match


def build_filter(
    start: datetime | None = None,
    end: datetime | None = None,
    city: str | None = None,
    restaurant: str | None = None,
    food_category: str | None = None,
    order_status: str | None = None,
    payment_method: str | None = None,
    search_order_id: str | None = None,
) -> dict:
    match = _filter_match(
        start=start,
        end=end,
        city=city,
        restaurant=restaurant,
        food_category=food_category,
        order_status=order_status,
        payment_method=payment_method,
    )
    if search_order_id:
        match["order_id"] = {"$regex": search_order_id, "$options": "i"}
    return match


def get_orders_page(
    match: dict,
    page: int = 1,
    page_size: int = 20,
    sort_field: str = "order_date",
    sort_dir: int = -1,
) -> tuple[list[dict], int]:
    """Return (records, total_count) for the given page."""
    total = count_orders(match)
    skip = (page - 1) * page_size
    records = fetch_orders_page(match, skip, page_size, sort_field, sort_dir)
    return records, total


def get_filter_options() -> dict:
    """Return distinct values for all dropdown filters."""
    return {
        "cities": ["All"] + distinct_values("city"),
        "restaurants": ["All"] + distinct_values("restaurant_name"),
        "categories": ["All"] + distinct_values("food_category"),
        "statuses": ["All"] + distinct_values("order_status"),
        "payments": ["All"] + distinct_values("payment_method"),
    }


def get_import_history(limit: int = 20) -> list[dict]:
    return fetch_import_logs(limit)
