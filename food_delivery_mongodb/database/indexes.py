"""
database/indexes.py
Creates and verifies MongoDB indexes for the food_delivery_analytics database.
Run once: python -m database.indexes
"""
import logging
from pymongo import ASCENDING, DESCENDING
from database.connection import get_db
from config.settings import settings

logger = logging.getLogger(__name__)


def create_indexes() -> dict:
    """Create all application indexes. Returns a summary dict."""
    db = get_db()
    results = {}

    # ── orders collection ────────────────────────────────────────────────────
    orders = db[settings.ORDERS_COLLECTION]

    # Unique index on order_id to prevent duplicate imports
    orders.create_index([("order_id", ASCENDING)], unique=True, name="order_id_unique")

    # Frequently filtered fields
    orders.create_index([("order_date", DESCENDING)], name="order_date_desc")
    orders.create_index([("city", ASCENDING)], name="city_asc")
    orders.create_index([("restaurant_name", ASCENDING)], name="restaurant_name_asc")
    orders.create_index([("food_category", ASCENDING)], name="food_category_asc")
    orders.create_index([("order_status", ASCENDING)], name="order_status_asc")
    orders.create_index([("payment_method", ASCENDING)], name="payment_method_asc")

    # Compound index for date + status (common aggregation pattern)
    orders.create_index(
        [("order_date", DESCENDING), ("order_status", ASCENDING)],
        name="date_status_compound",
    )

    results["orders"] = list(orders.index_information().keys())
    logger.info("Orders indexes: %s", results["orders"])

    # ── import_logs collection ───────────────────────────────────────────────
    logs = db[settings.IMPORT_LOGS_COLLECTION]
    logs.create_index([("imported_at", DESCENDING)], name="imported_at_desc")
    logs.create_index([("filename", ASCENDING)], name="filename_asc")
    results["import_logs"] = list(logs.index_information().keys())

    logger.info("Index creation complete.")
    return results


def list_indexes() -> dict:
    """Return existing indexes for each collection."""
    db = get_db()
    return {
        col: list(db[col].index_information().keys())
        for col in db.list_collection_names()
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    summary = create_indexes()
    for col, idx in summary.items():
        print(f"{col}: {idx}")
