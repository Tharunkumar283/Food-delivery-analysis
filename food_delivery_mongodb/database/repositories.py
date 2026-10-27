"""
database/repositories.py
Low-level CRUD helpers for each collection.
All heavy analytics live in analytics/aggregations.py.
"""
import logging
from datetime import datetime, timezone
from typing import Any

from pymongo import UpdateOne
from pymongo.errors import BulkWriteError

from database.connection import get_collection
from config.settings import settings

logger = logging.getLogger(__name__)


# ── Orders ───────────────────────────────────────────────────────────────────

def bulk_upsert_orders(docs: list[dict]) -> dict:
    """
    Insert / update orders using order_id as the unique key.
    Returns {"inserted": int, "updated": int, "errors": int}
    """
    if not docs:
        return {"inserted": 0, "updated": 0, "errors": 0}

    col = get_collection(settings.ORDERS_COLLECTION)
    ops = [
        UpdateOne({"order_id": d["order_id"]}, {"$setOnInsert": d}, upsert=True)
        for d in docs
    ]
    try:
        result = col.bulk_write(ops, ordered=False)
        return {
            "inserted": result.upserted_count,
            "updated": result.modified_count,
            "errors": 0,
        }
    except BulkWriteError as exc:
        write_errors = exc.details.get("writeErrors", [])
        return {
            "inserted": exc.details.get("nInserted", 0),
            "updated": exc.details.get("nModified", 0),
            "errors": len(write_errors),
        }


def count_orders(match: dict | None = None) -> int:
    col = get_collection(settings.ORDERS_COLLECTION)
    return col.count_documents(match or {})


def fetch_orders_page(
    match: dict,
    skip: int,
    limit: int,
    sort_field: str = "order_date",
    sort_dir: int = -1,
) -> list[dict]:
    col = get_collection(settings.ORDERS_COLLECTION)
    cursor = (
        col.find(match, {"_id": 0})
        .sort(sort_field, sort_dir)
        .skip(skip)
        .limit(limit)
    )
    return list(cursor)


def fetch_order_by_id(order_id: str) -> dict | None:
    col = get_collection(settings.ORDERS_COLLECTION)
    return col.find_one({"order_id": order_id}, {"_id": 0})


def distinct_values(field: str) -> list:
    col = get_collection(settings.ORDERS_COLLECTION)
    return sorted(col.distinct(field))


# ── Import Logs ──────────────────────────────────────────────────────────────

def log_import(
    filename: str,
    total_rows: int,
    inserted: int,
    updated: int,
    rejected: int,
    skipped: int,
    errors: list[str],
) -> str:
    col = get_collection(settings.IMPORT_LOGS_COLLECTION)
    doc = {
        "filename": filename,
        "imported_at": datetime.now(timezone.utc),
        "total_rows": total_rows,
        "inserted": inserted,
        "updated": updated,
        "rejected": rejected,
        "skipped": skipped,
        "errors": errors[:50],  # keep at most 50 error messages
    }
    result = col.insert_one(doc)
    return str(result.inserted_id)


def fetch_import_logs(limit: int = 20) -> list[dict]:
    col = get_collection(settings.IMPORT_LOGS_COLLECTION)
    return list(
        col.find({}, {"_id": 0}).sort("imported_at", -1).limit(limit)
    )
