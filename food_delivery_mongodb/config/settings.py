"""
config/settings.py
Application-wide configuration loaded from environment variables.
"""
import os
from dotenv import load_dotenv

# Load .env from the project root (one level up from config/)
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_root, ".env"))


class Settings:
    # ── MongoDB ──────────────────────────────────────────────────────────────
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    DB_NAME: str = os.getenv("DB_NAME", "food_delivery_analytics")

    # Collection names
    ORDERS_COLLECTION: str = "orders"
    RESTAURANTS_COLLECTION: str = "restaurants"
    CUSTOMERS_COLLECTION: str = "customers"
    IMPORT_LOGS_COLLECTION: str = "import_logs"

    # ── Application ──────────────────────────────────────────────────────────
    APP_TITLE: str = os.getenv("APP_TITLE", "Online Food Delivery Analysis")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # ── Data ingestion ───────────────────────────────────────────────────────
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))

    # Canonical column mapping: CSV column -> internal field name.
    # Add aliases to support different CSV schemas.
    COLUMN_MAP: dict = {
        # order identifiers
        "order_id": "order_id",
        "orderid": "order_id",
        "id": "order_id",
        # dates
        "order_date": "order_date",
        "date": "order_date",
        "orderdate": "order_date",
        # customer
        "customer_id": "customer_id",
        "customerid": "customer_id",
        "customer": "customer_id",
        # restaurant
        "restaurant_id": "restaurant_id",
        "restaurantid": "restaurant_id",
        "restaurant_name": "restaurant_name",
        "restaurant": "restaurant_name",
        # location
        "city": "city",
        "location": "city",
        # food
        "food_category": "food_category",
        "category": "food_category",
        "item_name": "item_name",
        "item": "item_name",
        "food_item": "item_name",
        # order details
        "quantity": "quantity",
        "qty": "quantity",
        "item_price": "item_price",
        "price": "item_price",
        "unit_price": "item_price",
        "discount": "discount",
        "discount_amount": "discount",
        "delivery_fee": "delivery_fee",
        "delivery_charge": "delivery_fee",
        "total_amount": "total_amount",
        "total": "total_amount",
        "order_total": "total_amount",
        # payment & status
        "payment_method": "payment_method",
        "payment": "payment_method",
        "order_status": "order_status",
        "status": "order_status",
        # delivery
        "delivery_time_minutes": "delivery_time_minutes",
        "delivery_time": "delivery_time_minutes",
        "delivery_minutes": "delivery_time_minutes",
        # ratings
        "customer_rating": "customer_rating",
        "rating": "customer_rating",
        "review_score": "customer_rating",
    }

    # Fields that must be present after mapping
    REQUIRED_FIELDS: list = ["order_id", "order_date", "restaurant_name", "total_amount"]

    # Valid order statuses (case-insensitive)
    VALID_ORDER_STATUSES: set = {
        "completed", "delivered", "cancelled", "canceled",
        "pending", "processing", "failed",
    }

    # Valid payment methods (case-insensitive)
    VALID_PAYMENT_METHODS: set = {
        "credit card", "debit card", "cash", "upi", "wallet",
        "net banking", "paypal", "cod", "online",
    }


settings = Settings()
