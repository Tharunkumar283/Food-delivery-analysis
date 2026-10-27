"""
utils/export.py
CSV export helpers that respect active filters and strip internal fields.
"""
import io
import pandas as pd
from database.repositories import fetch_orders_page, count_orders


_SENSITIVE_FIELDS = {"customer_id", "_id"}
_MAX_EXPORT_ROWS = 50_000


def export_orders_csv(match: dict) -> bytes:
    """
    Export filtered orders as CSV bytes (UTF-8 with BOM for Excel compatibility).
    Caps at MAX_EXPORT_ROWS to prevent memory issues.
    """
    total = count_orders(match)
    limit = min(total, _MAX_EXPORT_ROWS)
    records = fetch_orders_page(match, skip=0, limit=limit, sort_field="order_date", sort_dir=-1)

    if not records:
        return b""

    df = pd.DataFrame(records)

    # Drop sensitive / internal fields
    for col in list(_SENSITIVE_FIELDS):
        if col in df.columns:
            df = df.drop(columns=[col])

    # Format dates
    if "order_date" in df.columns:
        df["order_date"] = pd.to_datetime(df["order_date"]).dt.strftime("%Y-%m-%d %H:%M")

    buf = io.StringIO()
    df.to_csv(buf, index=False, encoding="utf-8")
    return buf.getvalue().encode("utf-8-sig")  # utf-8-sig for Excel


def export_summary_csv(summary_data: list[dict], label: str = "summary") -> bytes:
    """Export a summary table (list of dicts) as CSV bytes."""
    if not summary_data:
        return b""
    buf = io.StringIO()
    pd.DataFrame(summary_data).to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8-sig")
