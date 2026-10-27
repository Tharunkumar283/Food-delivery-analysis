"""
analytics/advanced.py
Advanced MongoDB aggregation pipelines for:
  - RFM (Recency, Frequency, Monetary) customer segmentation
  - Repeat-customer / loyalty analysis
  - Discount impact analysis
  - Customer lifetime value (CLV) estimation

All heavy computation runs inside MongoDB via aggregation pipelines.
"""
import logging
from datetime import datetime, timezone
from typing import Any

from database.connection import get_collection
from config.settings import settings
from analytics.aggregations import _filter_match

logger = logging.getLogger(__name__)
COL = settings.ORDERS_COLLECTION


def _col():
    return get_collection(COL)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  RFM CUSTOMER SEGMENTATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_rfm_data(**kwargs) -> list[dict]:
    """
    RFM analysis per customer:
      - Recency:   days since last order (from most recent order in dataset)
      - Frequency: total number of orders
      - Monetary:  total spend on completed/delivered orders
    Returns a list of dicts sorted by monetary value descending.
    """
    match = _filter_match(**kwargs)

    # First, find the reference date (most recent order) in a separate pipeline
    ref_pipeline = [
        {"$match": match} if match else {"$match": {}},
        {"$group": {"_id": None, "max_date": {"$max": "$order_date"}}},
    ]
    ref_result = list(_col().aggregate(ref_pipeline))
    if not ref_result:
        return []
    ref_date = ref_result[0]["max_date"]

    # Main RFM pipeline
    pipeline = [
        {"$match": {**match, "customer_id": {"$ne": None}}},
        {
            "$group": {
                "_id": "$customer_id",
                "last_order": {"$max": "$order_date"},
                "first_order": {"$min": "$order_date"},
                "frequency": {"$sum": 1},
                "monetary": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["$order_status", ["Completed", "Delivered"]]},
                            {"$ifNull": ["$total_amount", 0]},
                            0,
                        ]
                    }
                },
                "total_orders": {"$sum": 1},
                "completed_orders": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["$order_status", ["Completed", "Delivered"]]},
                            1, 0,
                        ]
                    }
                },
                "avg_order_value": {"$avg": {"$ifNull": ["$total_amount", 0]}},
                "avg_rating": {"$avg": "$customer_rating"},
            }
        },
        {
            "$project": {
                "customer_id": "$_id",
                "_id": 0,
                "last_order": 1,
                "first_order": 1,
                "frequency": 1,
                "monetary": {"$round": ["$monetary", 2]},
                "total_orders": 1,
                "completed_orders": 1,
                "avg_order_value": {"$round": ["$avg_order_value", 2]},
                "avg_rating": {"$round": [{"$ifNull": ["$avg_rating", 0]}, 1]},
                "recency_days": {
                    "$round": [
                        {
                            "$divide": [
                                {"$subtract": [ref_date, "$last_order"]},
                                86400000,  # ms per day
                            ]
                        },
                        0,
                    ]
                },
            }
        },
        {"$sort": {"monetary": -1}},
    ]
    return list(_col().aggregate(pipeline))


def get_rfm_segments(**kwargs) -> list[dict]:
    """
    Assign RFM segments using MongoDB percentile boundaries.
    Segments: Champions, Loyal, Potential, At Risk, Hibernating, Lost.
    """
    rfm_data = get_rfm_data(**kwargs)
    if not rfm_data:
        return []

    # Calculate percentile boundaries in Python (lightweight — only summary stats)
    frequencies = sorted([r["frequency"] for r in rfm_data])
    monetaries = sorted([r["monetary"] for r in rfm_data])
    recencies = sorted([r["recency_days"] for r in rfm_data])

    def percentile(arr, p):
        idx = int(len(arr) * p / 100)
        return arr[min(idx, len(arr) - 1)]

    f_p33, f_p66 = percentile(frequencies, 33), percentile(frequencies, 66)
    m_p33, m_p66 = percentile(monetaries, 33), percentile(monetaries, 66)
    r_p33, r_p66 = percentile(recencies, 33), percentile(recencies, 66)

    def score(val, p33, p66, invert=False):
        """Score 1-3; invert=True for recency (lower is better)."""
        if invert:
            if val <= p33:
                return 3
            elif val <= p66:
                return 2
            return 1
        else:
            if val >= p66:
                return 3
            elif val >= p33:
                return 2
            return 1

    def segment_label(r_score, f_score, m_score):
        total = r_score + f_score + m_score
        if total >= 8:
            return "Champions"
        elif total >= 6:
            return "Loyal"
        elif r_score >= 2 and f_score <= 2:
            return "Potential"
        elif r_score <= 1 and f_score >= 2:
            return "At Risk"
        elif r_score <= 1 and f_score <= 1:
            return "Lost"
        else:
            return "Hibernating"

    for rec in rfm_data:
        r_s = score(rec["recency_days"], r_p33, r_p66, invert=True)
        f_s = score(rec["frequency"], f_p33, f_p66)
        m_s = score(rec["monetary"], m_p33, m_p66)
        rec["r_score"] = r_s
        rec["f_score"] = f_s
        rec["m_score"] = m_s
        rec["rfm_score"] = r_s + f_s + m_s
        rec["segment"] = segment_label(r_s, f_s, m_s)

    return rfm_data


def get_segment_summary(**kwargs) -> list[dict]:
    """Aggregate RFM segments into a summary table."""
    segments = get_rfm_segments(**kwargs)
    if not segments:
        return []

    from collections import defaultdict
    summary: dict[str, dict] = defaultdict(
        lambda: {"segment": "", "customers": 0, "total_orders": 0,
                 "total_revenue": 0.0, "avg_recency": 0.0, "avg_frequency": 0.0,
                 "avg_monetary": 0.0}
    )

    for s in segments:
        seg = s["segment"]
        d = summary[seg]
        d["segment"] = seg
        d["customers"] += 1
        d["total_orders"] += s["frequency"]
        d["total_revenue"] += s["monetary"]
        d["avg_recency"] += s["recency_days"]
        d["avg_frequency"] += s["frequency"]
        d["avg_monetary"] += s["monetary"]

    result = []
    for seg, d in summary.items():
        n = d["customers"]
        result.append({
            "segment": seg,
            "customers": n,
            "total_orders": d["total_orders"],
            "total_revenue": round(d["total_revenue"], 2),
            "avg_recency": round(d["avg_recency"] / max(n, 1), 1),
            "avg_frequency": round(d["avg_frequency"] / max(n, 1), 1),
            "avg_monetary": round(d["avg_monetary"] / max(n, 1), 2),
        })
    result.sort(key=lambda x: x["total_revenue"], reverse=True)
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  REPEAT CUSTOMER ANALYSIS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_repeat_customer_stats(**kwargs) -> dict:
    """
    Overall repeat-customer metrics:
      - Total unique customers
      - One-time vs repeat customers
      - Repeat rate
      - Revenue share from repeat customers
    """
    match = _filter_match(**kwargs)
    pipeline = [
        {"$match": {**match, "customer_id": {"$ne": None}}},
        {
            "$group": {
                "_id": "$customer_id",
                "order_count": {"$sum": 1},
                "total_spent": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["$order_status", ["Completed", "Delivered"]]},
                            {"$ifNull": ["$total_amount", 0]},
                            0,
                        ]
                    }
                },
            }
        },
        {
            "$group": {
                "_id": None,
                "total_customers": {"$sum": 1},
                "one_time": {
                    "$sum": {"$cond": [{"$eq": ["$order_count", 1]}, 1, 0]}
                },
                "repeat": {
                    "$sum": {"$cond": [{"$gt": ["$order_count", 1]}, 1, 0]}
                },
                "total_revenue": {"$sum": "$total_spent"},
                "repeat_revenue": {
                    "$sum": {
                        "$cond": [
                            {"$gt": ["$order_count", 1]},
                            "$total_spent",
                            0,
                        ]
                    }
                },
                "avg_orders_per_customer": {"$avg": "$order_count"},
                "max_orders": {"$max": "$order_count"},
            }
        },
    ]
    result = list(_col().aggregate(pipeline))
    if not result:
        return {
            "total_customers": 0, "one_time": 0, "repeat": 0,
            "repeat_rate": 0.0, "total_revenue": 0.0, "repeat_revenue": 0.0,
            "repeat_revenue_share": 0.0, "avg_orders_per_customer": 0.0,
            "max_orders": 0,
        }
    r = result[0]
    r.pop("_id", None)
    total = r.get("total_customers", 0) or 1
    r["repeat_rate"] = round(r.get("repeat", 0) / total * 100, 2)
    rev = r.get("total_revenue", 0) or 1
    r["repeat_revenue_share"] = round(r.get("repeat_revenue", 0) / rev * 100, 2)
    r["avg_orders_per_customer"] = round(r.get("avg_orders_per_customer", 0), 1)
    return r


def get_order_frequency_distribution(**kwargs) -> list[dict]:
    """
    Distribution of customers by number of orders placed.
    Returns [{order_count: 1, customers: 45}, {order_count: 2, customers: 30}, ...]
    """
    match = _filter_match(**kwargs)
    pipeline = [
        {"$match": {**match, "customer_id": {"$ne": None}}},
        {"$group": {"_id": "$customer_id", "order_count": {"$sum": 1}}},
        {"$group": {"_id": "$order_count", "customers": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
        {"$project": {"order_count": "$_id", "customers": 1, "_id": 0}},
    ]
    return list(_col().aggregate(pipeline))


def get_top_loyal_customers(limit: int = 20, **kwargs) -> list[dict]:
    """Top customers by total order count with their revenue and ratings."""
    match = _filter_match(**kwargs)
    pipeline = [
        {"$match": {**match, "customer_id": {"$ne": None}}},
        {
            "$group": {
                "_id": "$customer_id",
                "total_orders": {"$sum": 1},
                "total_spent": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["$order_status", ["Completed", "Delivered"]]},
                            {"$ifNull": ["$total_amount", 0]},
                            0,
                        ]
                    }
                },
                "avg_rating": {"$avg": "$customer_rating"},
                "first_order": {"$min": "$order_date"},
                "last_order": {"$max": "$order_date"},
                "cities": {"$addToSet": "$city"},
                "restaurants": {"$addToSet": "$restaurant_name"},
                "cancelled": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["$order_status", ["Cancelled", "Canceled"]]},
                            1, 0,
                        ]
                    }
                },
            }
        },
        {"$sort": {"total_orders": -1}},
        {"$limit": limit},
        {
            "$project": {
                "customer_id": "$_id",
                "_id": 0,
                "total_orders": 1,
                "total_spent": {"$round": ["$total_spent", 2]},
                "avg_rating": {"$round": [{"$ifNull": ["$avg_rating", 0]}, 1]},
                "first_order": 1,
                "last_order": 1,
                "unique_cities": {"$size": "$cities"},
                "unique_restaurants": {"$size": "$restaurants"},
                "cancelled": 1,
            }
        },
    ]
    return list(_col().aggregate(pipeline))


def get_customer_retention_by_month(**kwargs) -> list[dict]:
    """
    Monthly new vs returning customers.
    A customer is 'new' in the month of their first order.
    """
    match = _filter_match(**kwargs)
    # Step 1: Get first-order month for each customer
    # Step 2: For each order, check if it's in the first-order month
    pipeline = [
        {"$match": {**match, "customer_id": {"$ne": None}}},
        {
            "$group": {
                "_id": {
                    "customer": "$customer_id",
                    "month": {"$dateToString": {"format": "%Y-%m", "date": "$order_date"}},
                },
                "first_order_date": {"$min": "$order_date"},
                "orders": {"$sum": 1},
            }
        },
        {
            "$addFields": {
                "first_month": {
                    "$dateToString": {"format": "%Y-%m", "date": "$first_order_date"}
                },
            }
        },
        # For each customer-month, determine if new or returning
        {
            "$group": {
                "_id": "$_id.month",
                "total_customers": {"$sum": 1},
                "new_customers": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$_id.month", "$first_month"]},
                            1, 0,
                        ]
                    }
                },
                "returning_customers": {
                    "$sum": {
                        "$cond": [
                            {"$ne": ["$_id.month", "$first_month"]},
                            1, 0,
                        ]
                    }
                },
            }
        },
        {"$sort": {"_id": 1}},
        {
            "$project": {
                "month": "$_id",
                "_id": 0,
                "total_customers": 1,
                "new_customers": 1,
                "returning_customers": 1,
            }
        },
    ]
    return list(_col().aggregate(pipeline))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DISCOUNT IMPACT ANALYSIS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_discount_overview(**kwargs) -> dict:
    """
    Discount usage stats:
      - Total orders with/without discount
      - Average discount value
      - Revenue with vs without discount
      - Avg rating comparison
    """
    match = _filter_match(**kwargs)
    pipeline = [
        {"$match": match} if match else {"$match": {}},
        {
            "$group": {
                "_id": None,
                "total_orders": {"$sum": 1},
                "orders_with_discount": {
                    "$sum": {
                        "$cond": [
                            {"$and": [
                                {"$ne": [{"$ifNull": ["$discount", 0]}, 0]},
                                {"$gt": [{"$ifNull": ["$discount", 0]}, 0]},
                            ]},
                            1, 0,
                        ]
                    }
                },
                "orders_without_discount": {
                    "$sum": {
                        "$cond": [
                            {"$or": [
                                {"$eq": [{"$ifNull": ["$discount", 0]}, 0]},
                                {"$lte": [{"$ifNull": ["$discount", 0]}, 0]},
                            ]},
                            1, 0,
                        ]
                    }
                },
                "total_discount_given": {
                    "$sum": {"$ifNull": ["$discount", 0]}
                },
                "avg_discount": {
                    "$avg": {
                        "$cond": [
                            {"$gt": [{"$ifNull": ["$discount", 0]}, 0]},
                            "$discount",
                            None,
                        ]
                    }
                },
                "revenue_with_discount": {
                    "$sum": {
                        "$cond": [
                            {"$and": [
                                {"$gt": [{"$ifNull": ["$discount", 0]}, 0]},
                                {"$in": ["$order_status", ["Completed", "Delivered"]]},
                            ]},
                            {"$ifNull": ["$total_amount", 0]},
                            0,
                        ]
                    }
                },
                "revenue_without_discount": {
                    "$sum": {
                        "$cond": [
                            {"$and": [
                                {"$lte": [{"$ifNull": ["$discount", 0]}, 0]},
                                {"$in": ["$order_status", ["Completed", "Delivered"]]},
                            ]},
                            {"$ifNull": ["$total_amount", 0]},
                            0,
                        ]
                    }
                },
                "avg_rating_with_discount": {
                    "$avg": {
                        "$cond": [
                            {"$and": [
                                {"$gt": [{"$ifNull": ["$discount", 0]}, 0]},
                                {"$ne": ["$customer_rating", None]},
                            ]},
                            "$customer_rating",
                            None,
                        ]
                    }
                },
                "avg_rating_without_discount": {
                    "$avg": {
                        "$cond": [
                            {"$and": [
                                {"$lte": [{"$ifNull": ["$discount", 0]}, 0]},
                                {"$ne": ["$customer_rating", None]},
                            ]},
                            "$customer_rating",
                            None,
                        ]
                    }
                },
                "avg_order_with_discount": {
                    "$avg": {
                        "$cond": [
                            {"$gt": [{"$ifNull": ["$discount", 0]}, 0]},
                            {"$ifNull": ["$total_amount", 0]},
                            None,
                        ]
                    }
                },
                "avg_order_without_discount": {
                    "$avg": {
                        "$cond": [
                            {"$lte": [{"$ifNull": ["$discount", 0]}, 0]},
                            {"$ifNull": ["$total_amount", 0]},
                            None,
                        ]
                    }
                },
            }
        },
    ]
    result = list(_col().aggregate(pipeline))
    if not result:
        return {
            "total_orders": 0, "orders_with_discount": 0,
            "orders_without_discount": 0, "total_discount_given": 0,
            "avg_discount": 0, "revenue_with_discount": 0,
            "revenue_without_discount": 0, "avg_rating_with_discount": 0,
            "avg_rating_without_discount": 0, "avg_order_with_discount": 0,
            "avg_order_without_discount": 0, "discount_usage_rate": 0,
        }
    r = result[0]
    r.pop("_id", None)
    total = r.get("total_orders", 0) or 1
    r["discount_usage_rate"] = round(
        r.get("orders_with_discount", 0) / total * 100, 2
    )
    return r


def get_discount_bands(**kwargs) -> list[dict]:
    """
    Group orders by discount percentage band.
    Returns [{band: "0%", orders: 400, avg_total: 500, ...}, ...]
    """
    match = _filter_match(**kwargs)
    pipeline = [
        {"$match": match} if match else {"$match": {}},
        {
            "$addFields": {
                "discount_pct": {
                    "$cond": [
                        {"$gt": [{"$ifNull": ["$item_price", 0]}, 0]},
                        {
                            "$multiply": [
                                {"$divide": [
                                    {"$ifNull": ["$discount", 0]},
                                    {"$multiply": [
                                        {"$ifNull": ["$item_price", 1]},
                                        {"$max": [{"$ifNull": ["$quantity", 1]}, 1]},
                                    ]},
                                ]},
                                100,
                            ]
                        },
                        0,
                    ]
                }
            }
        },
        {
            "$addFields": {
                "band": {
                    "$switch": {
                        "branches": [
                            {"case": {"$lte": ["$discount_pct", 0]}, "then": "No Discount"},
                            {"case": {"$lte": ["$discount_pct", 5]}, "then": "1-5%"},
                            {"case": {"$lte": ["$discount_pct", 10]}, "then": "5-10%"},
                            {"case": {"$lte": ["$discount_pct", 15]}, "then": "10-15%"},
                            {"case": {"$lte": ["$discount_pct", 20]}, "then": "15-20%"},
                            {"case": {"$lte": ["$discount_pct", 30]}, "then": "20-30%"},
                        ],
                        "default": "30%+",
                    }
                }
            }
        },
        {
            "$group": {
                "_id": "$band",
                "orders": {"$sum": 1},
                "avg_total": {"$avg": {"$ifNull": ["$total_amount", 0]}},
                "total_revenue": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["$order_status", ["Completed", "Delivered"]]},
                            {"$ifNull": ["$total_amount", 0]},
                            0,
                        ]
                    }
                },
                "avg_rating": {"$avg": "$customer_rating"},
                "cancellation_count": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["$order_status", ["Cancelled", "Canceled"]]},
                            1, 0,
                        ]
                    }
                },
            }
        },
        {
            "$project": {
                "band": "$_id",
                "_id": 0,
                "orders": 1,
                "avg_total": {"$round": ["$avg_total", 2]},
                "total_revenue": {"$round": ["$total_revenue", 2]},
                "avg_rating": {"$round": [{"$ifNull": ["$avg_rating", 0]}, 1]},
                "cancellation_rate": {
                    "$round": [
                        {"$multiply": [
                            {"$divide": ["$cancellation_count", {"$max": ["$orders", 1]}]},
                            100,
                        ]},
                        1,
                    ]
                },
            }
        },
        {"$sort": {"orders": -1}},
    ]
    return list(_col().aggregate(pipeline))


def get_discount_trend_by_month(**kwargs) -> list[dict]:
    """
    Monthly trend: avg discount, discount usage rate, avg order value.
    """
    match = _filter_match(**kwargs)
    pipeline = [
        {"$match": match} if match else {"$match": {}},
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m", "date": "$order_date"}},
                "total_orders": {"$sum": 1},
                "discounted_orders": {
                    "$sum": {
                        "$cond": [
                            {"$gt": [{"$ifNull": ["$discount", 0]}, 0]},
                            1, 0,
                        ]
                    }
                },
                "avg_discount": {
                    "$avg": {
                        "$cond": [
                            {"$gt": [{"$ifNull": ["$discount", 0]}, 0]},
                            "$discount",
                            None,
                        ]
                    }
                },
                "total_discount": {"$sum": {"$ifNull": ["$discount", 0]}},
                "avg_order_value": {"$avg": {"$ifNull": ["$total_amount", 0]}},
            }
        },
        {"$sort": {"_id": 1}},
        {
            "$project": {
                "month": "$_id",
                "_id": 0,
                "total_orders": 1,
                "discounted_orders": 1,
                "discount_rate": {
                    "$round": [
                        {"$multiply": [
                            {"$divide": ["$discounted_orders", {"$max": ["$total_orders", 1]}]},
                            100,
                        ]},
                        1,
                    ]
                },
                "avg_discount": {"$round": [{"$ifNull": ["$avg_discount", 0]}, 2]},
                "total_discount": {"$round": ["$total_discount", 2]},
                "avg_order_value": {"$round": ["$avg_order_value", 2]},
            }
        },
    ]
    return list(_col().aggregate(pipeline))


def get_discount_by_category(**kwargs) -> list[dict]:
    """Average discount and discount frequency by food category."""
    match = _filter_match(**kwargs)
    pipeline = [
        {"$match": {**match, "food_category": {"$ne": None}}},
        {
            "$group": {
                "_id": "$food_category",
                "total_orders": {"$sum": 1},
                "discounted_orders": {
                    "$sum": {
                        "$cond": [
                            {"$gt": [{"$ifNull": ["$discount", 0]}, 0]},
                            1, 0,
                        ]
                    }
                },
                "avg_discount": {
                    "$avg": {
                        "$cond": [
                            {"$gt": [{"$ifNull": ["$discount", 0]}, 0]},
                            "$discount",
                            None,
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
                "avg_rating": {"$avg": "$customer_rating"},
            }
        },
        {"$sort": {"total_orders": -1}},
        {
            "$project": {
                "category": "$_id",
                "_id": 0,
                "total_orders": 1,
                "discounted_orders": 1,
                "discount_rate": {
                    "$round": [
                        {"$multiply": [
                            {"$divide": ["$discounted_orders", {"$max": ["$total_orders", 1]}]},
                            100,
                        ]},
                        1,
                    ]
                },
                "avg_discount": {"$round": [{"$ifNull": ["$avg_discount", 0]}, 2]},
                "total_revenue": {"$round": ["$total_revenue", 2]},
                "avg_rating": {"$round": [{"$ifNull": ["$avg_rating", 0]}, 1]},
            }
        },
    ]
    return list(_col().aggregate(pipeline))
