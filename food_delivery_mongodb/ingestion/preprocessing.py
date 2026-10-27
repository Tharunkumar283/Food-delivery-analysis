"""
ingestion/preprocessing.py
Cleans and normalises raw DataFrame chunks before validation.
"""
import re
import logging
import numpy as np
import pandas as pd
from config.settings import settings

logger = logging.getLogger(__name__)


def normalise_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase, strip whitespace, replace spaces/hyphens with underscores."""
    df.columns = [
        re.sub(r"[\s\-]+", "_", c.strip().lower()) for c in df.columns
    ]
    return df


def apply_column_mapping(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns according to settings.COLUMN_MAP."""
    mapping = {
        col: settings.COLUMN_MAP[col]
        for col in df.columns
        if col in settings.COLUMN_MAP
    }
    return df.rename(columns=mapping)


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all cleaning steps:
    1. Normalise / map column names.
    2. Drop fully empty rows.
    3. Strip string whitespace.
    4. Parse order_date to datetime.
    5. Coerce numeric columns.
    6. Fill sensible defaults for optional numeric fields.
    """
    df = normalise_column_names(df)
    df = apply_column_mapping(df)
    df = df.dropna(how="all")

    # Strip whitespace from all string columns
    str_cols = df.select_dtypes(include=["object", "str"]).columns
    for col in str_cols:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"nan": None, "": None, "NaN": None, "None": None})

    # Parse order_date
    if "order_date" in df.columns:
        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")

    # Coerce numeric columns
    numeric_cols = [
        "quantity", "item_price", "discount", "delivery_fee",
        "total_amount", "delivery_time_minutes", "customer_rating",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Default missing optional numerics to 0
    for col in ["discount", "delivery_fee"]:
        if col in df.columns:
            df[col] = df[col].fillna(0.0)

    # Normalise text categoricals
    for col in ["order_status", "payment_method", "food_category", "city", "restaurant_name"]:
        if col in df.columns:
            df[col] = df[col].str.title().where(df[col].notna(), other=None)

    return df


def prepare_for_mongo(df: pd.DataFrame) -> list[dict]:
    """
    Convert cleaned DataFrame to list of dicts suitable for MongoDB insertion.
    Converts NaN → None, Timestamps → Python datetime.
    """
    records = []
    for rec in df.to_dict(orient="records"):
        cleaned = {}
        for k, v in rec.items():
            if isinstance(v, float) and np.isnan(v):
                cleaned[k] = None
            elif isinstance(v, pd.Timestamp):
                cleaned[k] = v.to_pydatetime() if not pd.isna(v) else None
            else:
                cleaned[k] = v
        records.append(cleaned)
    return records
