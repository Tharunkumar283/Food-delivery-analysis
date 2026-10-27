"""
analytics/aggregations.py
All MongoDB aggregation pipelines. Every pipeline runs inside MongoDB
so that Python only receives the summarised result set.
"""
import logging
from datetime import datetime, timezone
from typing import Any

from database.connection import get_collection
from config.settings import settings

logger = logging.getLogger(__name__)
COL = settings.ORDERS_COLLECTION


def _col():
    return get_collection(COL)


def _date_match(start: datetime | None, end: datetime | None) -> dict:
    """Build a $match clause for order_date range (both optional)."""
    range_clause: dict[str, Any] = {}
    if start:
        range_clause["$gte"] = start
    if end:
        range_clause["$lte"] = end
    return {"order_date": range_clause} if range_clause else {}


def _filter_match(
    start: datetime | None = None,
    end: datetime | None = None,
    city: str | None = None,
    restaurant: str | None = None,
    food_category: str | None = None,
    order_status: str | None = None,
    payment_method: str | None = None,
    **kwargs,
) -> dict:
    """Build a combined $match filter dict from all global filter params."""
    match: dict[str, Any] = {}
    if start or end:
        match.update(_date_match(start, end))
    if city:
        match["city"] = city
    if restaurant:
        match["restaurant_name"] = restaurant
    if food_category:
        match["food_category"] = food_category
    if order_status:
        match["order_status"] = order_status
    if payment_method:
        match["payment_method"] = payment_method
    return match


# ── Overview KPIs ─────────────────────────────────────────────────────────────

def get_overview_kpis(
    start: datetime | None = None,
    end: datetime | None = None,
    city: str | None = None,
    restaurant: str | None = None,
    food_category: str | None = None,
    order_status: str | None = None,
    payment_method: str | None = None,
    **kwargs,
) -> dict:
    match = _filter_match(
        start=start,
        end=end,
        city=city,
        restaurant=restaurant,
        food_category=food_category,
        order_status=order_status,
        payment_method=payment_method,
        **kwargs,
    )
    pipeline = [
        {"$match": match} if match else {"$match": {}},
        {
            "$group": {
                "_id": None,
                "total_orders": {"$sum": 1},
                "completed_orders": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["$order_status", ["Completed", "Delivered"]]},
                            1,
                            0,
                        ]
                    }
                },
                "cancelled_orders": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["$order_status", ["Cancelled", "Canceled"]]},
                            1,
                            0,
                        ]
                    }
                },
                "total_revenue": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["$order_status", ["Completed", "Delivered"]]},
                            {"$ifNull": ["$total_amount", 0]},
                            0,
                        ]
                    }
                },
                "avg_order_value": {"$avg": {"$ifNull": ["$total_amount", 0]}},
                "avg_delivery_time": {"$avg": "$delivery_time_minutes"},
                "avg_rating": {"$avg": "$customer_rating"},
            }
        },
    ]
    result = list(_col().aggregate(pipeline))
    if not result:
        return {
            "total_orders": 0,
            "completed_orders": 0,
            "cancelled_orders": 0,
            "total_revenue": 0.0,
            "avg_order_value": 0.0,
            "avg_delivery_time": 0.0,
            "avg_rating": 0.0,
            "cancellation_rate": 0.0,
        }
    r = result[0]
    r.pop("_id", None)
    total = r.get("total_orders", 0) or 1
    r["cancellation_rate"] = round(r.get("cancelled_orders", 0) / total * 100, 2)
    return r


# ── Revenue Trends ────────────────────────────────────────────────────────────

def get_revenue_by_day(
    start: datetime | None = None,
    end: datetime | None = None,
    **kwargs,
) -> list[dict]:
    match = _filter_match(start=start, end=end, **kwargs)
    pipeline = [
        {"$match": {**match, "order_status": {"$in": ["Completed", "Delivered"]}}},
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$order_date"}
                },
                "revenue": {"$sum": {"$ifNull": ["$total_amount", 0]}},
                "orders": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
        {"$project": {"date": "$_id", "revenue": 1, "orders": 1, "_id": 0}},
    ]
    return list(_col().aggregate(pipeline))


def get_revenue_by_month(
    start: datetime | None = None,
    end: datetime | None = None,
    **kwargs,
) -> list[dict]:
    match = _filter_match(start=start, end=end, **kwargs)
    pipeline = [
        {"$match": {**match, "order_status": {"$in": ["Completed", "Delivered"]}}},
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m", "date": "$order_date"}
                },
                "revenue": {"$sum": {"$ifNull": ["$total_amount", 0]}},
                "orders": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
        {"$project": {"month": "$_id", "revenue": 1, "orders": 1, "_id": 0}},
    ]
    return list(_col().aggregate(pipeline))


def get_revenue_by_week(
    start: datetime | None = None,
    end: datetime | None = None,
    **kwargs,
) -> list[dict]:
    match = _filter_match(start=start, end=end, **kwargs)
    pipeline = [
        {"$match": {**match, "order_status": {"$in": ["Completed", "Delivered"]}}},
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-W%V", "date": "$order_date"}
                },
                "revenue": {"$sum": {"$ifNull": ["$total_amount", 0]}},
                "orders": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
        {"$project": {"week": "$_id", "revenue": 1, "orders": 1, "_id": 0}},
    ]
    return list(_col().aggregate(pipeline))


# ── Category Analysis ─────────────────────────────────────────────────────────

def get_revenue_by_category(**kwargs) -> list[dict]:
    match = _filter_match(**kwargs)
    pipeline = [
        {"$match": {**match, "order_status": {"$in": ["Completed", "Delivered"]}}},
        {
            "$group": {
                "_id": "$food_category",
                "revenue": {"$sum": {"$ifNull": ["$total_amount", 0]}},
                "orders": {"$sum": 1},
            }
        },
        {"$sort": {"revenue": -1}},
        {"$project": {"category": "$_id", "revenue": 1, "orders": 1, "_id": 0}},
    ]
    return list(_col().aggregate(pipeline))


def get_orders_by_category(**kwargs) -> list[dict]:
    match = _filter_match(**kwargs)
    pipeline = [
        {"$match": match},
        {"$group": {"_id": "$food_category", "orders": {"$sum": 1}}},
        {"$sort": {"orders": -1}},
        {"$project": {"category": "$_id", "orders": 1, "_id": 0}},
    ]
    return list(_col().aggregate(pipeline))


# ── City Analysis ─────────────────────────────────────────────────────────────

def get_revenue_by_city(**kwargs) -> list[dict]:
    match = _filter_match(**kwargs)
    pipeline = [
        {"$match": {**match, "order_status": {"$in": ["Completed", "Delivered"]}}},
        {
            "$group": {
                "_id": "$city",
                "revenue": {"$sum": {"$ifNull": ["$total_amount", 0]}},
                "orders": {"$sum": 1},
                "avg_delivery": {"$avg": "$delivery_time_minutes"},
            }
        },
        {"$sort": {"revenue": -1}},
        {"$project": {"city": "$_id", "revenue": 1, "orders": 1, "avg_delivery": 1, "_id": 0}},
    ]
    return list(_col().aggregate(pipeline))


# ── Restaurant Analysis ───────────────────────────────────────────────────────

def get_top_restaurants_by_revenue(limit: int = 10, **kwargs) -> list[dict]:
    match = _filter_match(**kwargs)
    pipeline = [
        {"$match": {**match, "order_status": {"$in": ["Completed", "Delivered"]}}},
        {
            "$group": {
                "_id": "$restaurant_name",
                "revenue": {"$sum": {"$ifNull": ["$total_amount", 0]}},
                "orders": {"$sum": 1},
                "avg_rating": {"$avg": "$customer_rating"},
            }
        },
        {"$sort": {"revenue": -1}},
        {"$limit": limit},
        {"$project": {"restaurant": "$_id", "revenue": 1, "orders": 1, "avg_rating": 1, "_id": 0}},
    ]
    return list(_col().aggregate(pipeline))


def get_top_restaurants_by_orders(limit: int = 10, **kwargs) -> list[dict]:
    match = _filter_match(**kwargs)
    pipeline = [
        {"$match": match},
        {
            "$group": {
                "_id": "$restaurant_name",
                "orders": {"$sum": 1},
                "avg_delivery": {"$avg": "$delivery_time_minutes"},
                "avg_rating": {"$avg": "$customer_rating"},
                "cancelled": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["$order_status", ["Cancelled", "Canceled"]]},
                            1,
                            0,
                        ]
                    }
                },
            }
        },
        {"$sort": {"orders": -1}},
        {"$limit": limit},
        {
            "$project": {
                "restaurant": "$_id",
                "orders": 1,
                "avg_delivery": 1,
                "avg_rating": 1,
                "cancellation_rate": {
                    "$multiply": [
                        {"$divide": ["$cancelled", {"$max": ["$orders", 1]}]},
                        100,
                    ]
                },
                "_id": 0,
            }
        },
    ]
    return list(_col().aggregate(pipeline))


def get_restaurant_performance(**kwargs) -> list[dict]:
    """Full restaurant performance table."""
    match = _filter_match(**kwargs)
    pipeline = [
        {"$match": match},
        {
            "$group": {
                "_id": "$restaurant_name",
                "total_orders": {"$sum": 1},
                "completed": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["$order_status", ["Completed", "Delivered"]]},
                            1,
                            0,
                        ]
                    }
                },
                "cancelled": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["$order_status", ["Cancelled", "Canceled"]]},
                            1,
                            0,
                        ]
                    }
                },
                "revenue": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["$order_status", ["Completed", "Delivered"]]},
                            {"$ifNull": ["$total_amount", 0]},
                            0,
                        ]
                    }
                },
                "avg_delivery": {"$avg": "$delivery_time_minutes"},
                "avg_rating": {"$avg": "$customer_rating"},
            }
        },
        {"$sort": {"revenue": -1}},
        {
            "$project": {
                "restaurant": "$_id",
                "total_orders": 1,
                "completed": 1,
                "cancelled": 1,
                "revenue": 1,
                "avg_delivery": 1,
                "avg_rating": 1,
                "cancellation_rate": {
                    "$multiply": [
                        {"$divide": ["$cancelled", {"$max": ["$total_orders", 1]}]},
                        100,
                    ]
                },
                "_id": 0,
            }
        },
    ]
    return list(_col().aggregate(pipeline))


# ── Payment & Status Analysis ─────────────────────────────────────────────────

def get_payment_distribution(**kwargs) -> list[dict]:
    match = _filter_match(**kwargs)
    pipeline = [
        {"$match": match},
        {"$group": {"_id": "$payment_method", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$project": {"payment_method": "$_id", "count": 1, "_id": 0}},
    ]
    return list(_col().aggregate(pipeline))


def get_order_status_distribution(**kwargs) -> list[dict]:
    match = _filter_match(**kwargs)
    pipeline = [
        {"$match": match},
        {"$group": {"_id": "$order_status", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$project": {"status": "$_id", "count": 1, "_id": 0}},
    ]
    return list(_col().aggregate(pipeline))


# ── Time-of-day / weekday Analysis ───────────────────────────────────────────

def get_orders_by_hour(**kwargs) -> list[dict]:
    match = _filter_match(**kwargs)
    pipeline = [
        {"$match": match},
        {
            "$group": {
                "_id": {"$hour": "$order_date"},
                "orders": {"$sum": 1},
                "revenue": {"$sum": {"$ifNull": ["$total_amount", 0]}},
            }
        },
        {"$sort": {"_id": 1}},
        {"$project": {"hour": "$_id", "orders": 1, "revenue": 1, "_id": 0}},
    ]
    return list(_col().aggregate(pipeline))


def get_orders_by_weekday(**kwargs) -> list[dict]:
    """MongoDB $dayOfWeek: 1=Sunday, 7=Saturday."""
    match = _filter_match(**kwargs)
    pipeline = [
        {"$match": match},
        {
            "$group": {
                "_id": {"$dayOfWeek": "$order_date"},
                "orders": {"$sum": 1},
                "revenue": {"$sum": {"$ifNull": ["$total_amount", 0]}},
            }
        },
        {"$sort": {"_id": 1}},
        {"$project": {"day_num": "$_id", "orders": 1, "revenue": 1, "_id": 0}},
    ]
    raw = list(_col().aggregate(pipeline))
    day_names = {1: "Sun", 2: "Mon", 3: "Tue", 4: "Wed", 5: "Thu", 6: "Fri", 7: "Sat"}
    for r in raw:
        r["weekday"] = day_names.get(r["day_num"], str(r["day_num"]))
    return raw


# ── Delivery Analysis ─────────────────────────────────────────────────────────

def get_delivery_time_distribution(**kwargs) -> list[dict]:
    match = _filter_match(**kwargs)
    pipeline = [
        {"$match": {**match, "delivery_time_minutes": {"$ne": None, "$gt": 0}}},
        {
            "$bucket": {
                "groupBy": "$delivery_time_minutes",
                "boundaries": [0, 15, 30, 45, 60, 90, 120, 180, 300],
                "default": "300+",
                "output": {"count": {"$sum": 1}},
            }
        },
    ]
    try:
        return list(_col().aggregate(pipeline))
    except Exception:
        # Fallback if $bucket fails on empty data
        return []


def get_avg_delivery_by_city(**kwargs) -> list[dict]:
    match = _filter_match(**kwargs)
    pipeline = [
        {"$match": {**match, "delivery_time_minutes": {"$ne": None, "$gt": 0}}},
        {
            "$group": {
                "_id": "$city",
                "avg_delivery": {"$avg": "$delivery_time_minutes"},
                "orders": {"$sum": 1},
            }
        },
        {"$sort": {"avg_delivery": 1}},
        {"$project": {"city": "$_id", "avg_delivery": 1, "orders": 1, "_id": 0}},
    ]
    return list(_col().aggregate(pipeline))


def get_avg_delivery_by_restaurant(limit: int = 15, **kwargs) -> list[dict]:
    match = _filter_match(**kwargs)
    pipeline = [
        {"$match": {**match, "delivery_time_minutes": {"$ne": None, "$gt": 0}}},
        {
            "$group": {
                "_id": "$restaurant_name",
                "avg_delivery": {"$avg": "$delivery_time_minutes"},
                "orders": {"$sum": 1},
            }
        },
        {"$sort": {"avg_delivery": 1}},
        {"$limit": limit},
        {"$project": {"restaurant": "$_id", "avg_delivery": 1, "orders": 1, "_id": 0}},
    ]
    return list(_col().aggregate(pipeline))


# ── Rating Analysis ───────────────────────────────────────────────────────────

def get_rating_distribution(**kwargs) -> list[dict]:
    match = _filter_match(**kwargs)
    pipeline = [
        {"$match": {**match, "customer_rating": {"$ne": None}}},
        {
            "$group": {
                "_id": {"$floor": "$customer_rating"},
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
        {"$project": {"rating": "$_id", "count": 1, "_id": 0}},
    ]
    return list(_col().aggregate(pipeline))


def get_rating_by_restaurant(limit: int = 10, **kwargs) -> list[dict]:
    match = _filter_match(**kwargs)
    pipeline = [
        {"$match": {**match, "customer_rating": {"$ne": None}}},
        {
            "$group": {
                "_id": "$restaurant_name",
                "avg_rating": {"$avg": "$customer_rating"},
                "count": {"$sum": 1},
            }
        },
        {"$match": {"count": {"$gte": 5}}},
        {"$sort": {"avg_rating": -1}},
        {"$limit": limit},
        {"$project": {"restaurant": "$_id", "avg_rating": 1, "count": 1, "_id": 0}},
    ]
    return list(_col().aggregate(pipeline))


# ── Heatmap ───────────────────────────────────────────────────────────────────

def get_heatmap_data(**kwargs) -> list[dict]:
    """Orders grouped by weekday × hour for heatmap."""
    match = _filter_match(**kwargs)
    pipeline = [
        {"$match": match},
        {
            "$group": {
                "_id": {
                    "day": {"$dayOfWeek": "$order_date"},
                    "hour": {"$hour": "$order_date"},
                },
                "orders": {"$sum": 1},
            }
        },
        {
            "$project": {
                "day": "$_id.day",
                "hour": "$_id.hour",
                "orders": 1,
                "_id": 0,
            }
        },
    ]
    return list(_col().aggregate(pipeline))
