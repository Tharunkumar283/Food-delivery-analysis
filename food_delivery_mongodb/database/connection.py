"""
database/connection.py
MongoDB connection management with singleton pattern and safe error handling.
"""
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from config.settings import settings

logger = logging.getLogger(__name__)

_client: MongoClient | None = None


def get_client() -> MongoClient:
    """Return a reusable MongoClient (singleton per process)."""
    global _client
    if _client is None:
        try:
            _client = MongoClient(
                settings.MONGO_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
            )
            # Validate the connection immediately
            _client.admin.command("ping")
            logger.info("MongoDB connection established.")
        except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
            _client = None
            # Do NOT log the full URI (it may contain credentials)
            raise ConnectionError(
                "Unable to connect to MongoDB. "
                "Check MONGO_URI in your .env file and ensure the server is running."
            ) from exc
    return _client


def get_db():
    """Return the application database."""
    return get_client()[settings.DB_NAME]


def get_collection(name: str):
    """Return a named collection."""
    return get_db()[name]


def ping() -> bool:
    """Return True if the database is reachable, False otherwise."""
    try:
        get_client().admin.command("ping")
        return True
    except Exception:
        return False


def close_connection() -> None:
    """Close the MongoClient (call on app shutdown if needed)."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("MongoDB connection closed.")
