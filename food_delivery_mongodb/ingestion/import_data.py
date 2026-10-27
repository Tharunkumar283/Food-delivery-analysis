"""
ingestion/import_data.py
Entry point for importing CSV files into MongoDB.

Usage:
    python -m ingestion.import_data data/food_delivery_sample.csv
    python -m ingestion.import_data data/food_delivery_sample.csv --chunk-size 500
"""
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd

from config.settings import settings
from database.connection import get_db, ping
from database.indexes import create_indexes
from database.repositories import bulk_upsert_orders, log_import
from ingestion.preprocessing import clean_dataframe, prepare_for_mongo
from ingestion.validation import validate_batch

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def import_csv(
    filepath: str,
    chunk_size: int = settings.CHUNK_SIZE,
    progress_callback=None,
) -> dict:
    """
    Import a CSV file into MongoDB in chunks.

    Args:
        filepath:          Path to the CSV file.
        chunk_size:        Number of rows per processing batch.
        progress_callback: Optional callable(pct, message) for Streamlit progress.

    Returns:
        Summary dict with keys: total_rows, inserted, updated, rejected,
        skipped, errors, duration_seconds.
    """
    start = datetime.now(timezone.utc)
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {filepath}")
    if not path.suffix.lower() == ".csv":
        raise ValueError(f"Expected a .csv file, got: {path.suffix}")

    if not ping():
        raise ConnectionError(
            "Cannot reach MongoDB. Check your .env settings and that the server is running."
        )

    # Ensure indexes exist before bulk inserts
    create_indexes()

    totals = {
        "total_rows": 0,
        "inserted": 0,
        "updated": 0,
        "rejected": 0,
        "skipped": 0,
        "errors": 0,
    }
    all_rejection_msgs: list[str] = []

    logger.info("Starting import: %s (chunk_size=%d)", path.name, chunk_size)

    # Count total rows for progress bar (fast scan)
    try:
        total_row_count = sum(1 for _ in open(path, encoding="utf-8")) - 1  # -1 for header
    except Exception:
        total_row_count = None

    rows_processed = 0

    for chunk_df in pd.read_csv(
        path,
        chunksize=chunk_size,
        encoding="utf-8",
        low_memory=False,
    ):
        rows_processed += len(chunk_df)

        # -- Clean --
        try:
            clean_df = clean_dataframe(chunk_df)
        except Exception as exc:
            logger.warning("Chunk cleaning failed: %s", exc)
            totals["skipped"] += len(chunk_df)
            continue

        # -- Convert to dicts --
        records = prepare_for_mongo(clean_df)
        totals["total_rows"] += len(records)

        # -- Validate --
        valid, rejected = validate_batch(records)
        totals["rejected"] += len(rejected)
        for r in rejected:
            reasons = r.get("_rejection_reasons", [])
            oid = r.get("order_id", "<unknown>")
            for reason in reasons:
                all_rejection_msgs.append(f"order_id={oid}: {reason}")

        # -- Insert --
        if valid:
            result = bulk_upsert_orders(valid)
            totals["inserted"] += result["inserted"]
            totals["updated"] += result["updated"]
            totals["errors"] += result["errors"]

        # -- Progress --
        if progress_callback and total_row_count:
            pct = min(rows_processed / total_row_count, 1.0)
            progress_callback(pct, f"Processed {rows_processed:,} rows …")

    duration = (datetime.now(timezone.utc) - start).total_seconds()
    totals["duration_seconds"] = round(duration, 2)

    # Log import to MongoDB
    try:
        log_import(
            filename=path.name,
            total_rows=totals["total_rows"],
            inserted=totals["inserted"],
            updated=totals["updated"],
            rejected=totals["rejected"],
            skipped=totals["skipped"],
            errors=all_rejection_msgs,
        )
    except Exception as exc:
        logger.warning("Could not write import log: %s", exc)

    logger.info(
        "Import complete: %d inserted, %d updated, %d rejected, %d errors in %.1fs",
        totals["inserted"],
        totals["updated"],
        totals["rejected"],
        totals["errors"],
        duration,
    )

    if progress_callback:
        progress_callback(1.0, "Import complete.")

    return totals


def _cli_main():
    parser = argparse.ArgumentParser(
        description="Import a food-delivery CSV file into MongoDB."
    )
    parser.add_argument("filepath", help="Path to the CSV file")
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=settings.CHUNK_SIZE,
        help=f"Rows per batch (default {settings.CHUNK_SIZE})",
    )
    args = parser.parse_args()

    try:
        summary = import_csv(args.filepath, chunk_size=args.chunk_size)
        print("\n── Import Summary ──────────────────────────────")
        for k, v in summary.items():
            print(f"  {k:<22}: {v}")
        print("────────────────────────────────────────────────")
    except Exception as exc:
        print(f"\n[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    _cli_main()
