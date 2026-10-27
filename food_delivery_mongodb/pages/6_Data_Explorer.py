"""
pages/6_Data_Explorer.py
Searchable, paginated data explorer with CSV export and import history.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import math
from database.connection import ping
from analytics.queries import (
    build_filter,
    get_orders_page,
    get_filter_options,
    get_import_history,
)
from utils.export import export_orders_csv, export_summary_csv
from utils.helpers import sidebar_date_filter, sidebar_filter_select, section_header
from ingestion.import_data import import_csv

st.set_page_config(page_title="Data Explorer | Food Delivery Analytics", layout="wide")
st.markdown(
    "<style>.stApp{background:linear-gradient(160deg,#0d1117 0%,#111827 100%);}</style>",
    unsafe_allow_html=True,
)

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.header("🔍 Filters")
start_dt, end_dt = sidebar_date_filter("explorer")

if ping():
    opts = get_filter_options()
else:
    opts = {
        "cities": ["All"], "restaurants": ["All"],
        "categories": ["All"], "statuses": ["All"], "payments": ["All"],
    }

city = sidebar_filter_select(opts["cities"], "City", "ex_city")
restaurant = sidebar_filter_select(opts["restaurants"], "Restaurant", "ex_restaurant")
category = sidebar_filter_select(opts.get("categories", ["All"]), "Food Category", "ex_cat")
status = sidebar_filter_select(opts.get("statuses", ["All"]), "Order Status", "ex_status")
payment = sidebar_filter_select(opts.get("payments", ["All"]), "Payment Method", "ex_payment")

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <h1 style="background:linear-gradient(135deg,#a78bfa,#8b5cf6);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    font-size:30px;margin-bottom:4px;">🔍 Data Explorer</h1>
    <p style="color:#8892a4;margin-top:0;">Search, filter, and export order records</p>
    """,
    unsafe_allow_html=True,
)

if not ping():
    st.error("❌ MongoDB is not reachable.")
    st.stop()

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_explorer, tab_import, tab_logs = st.tabs(["📋 Order Records", "⬆️ Import Data", "📜 Import History"])

# ══════════════════════════════════════════════════════════════════════════════
# Tab 1: Order Records
# ══════════════════════════════════════════════════════════════════════════════
with tab_explorer:
    col_search, col_page_size = st.columns([3, 1])
    with col_search:
        search_id = st.text_input("🔎 Search by Order ID", placeholder="e.g. ORD001", key="search_id")
    with col_page_size:
        page_size = st.selectbox("Rows per page", [10, 20, 50, 100], index=1, key="page_size")

    match = build_filter(
        start=start_dt,
        end=end_dt,
        city=city,
        restaurant=restaurant,
        food_category=category,
        order_status=status,
        payment_method=payment,
        search_order_id=search_id.strip() if search_id else None,
    )

    records, total = get_orders_page(match, page=1, page_size=1)  # just count
    total_records, _ = get_orders_page.__wrapped__(match, 1, 1) if False else (None, None)

    # Proper count
    from database.repositories import count_orders
    total_records = count_orders(match)
    total_pages = max(1, math.ceil(total_records / page_size))

    st.markdown(
        f"<p style='color:#8892a4; font-size:14px;'>Found <b style='color:#e0e0e0'>{total_records:,}</b> records</p>",
        unsafe_allow_html=True,
    )

    # Pagination
    col_prev, col_pnum, col_next = st.columns([1, 3, 1])
    with col_pnum:
        page = st.number_input(
            f"Page (of {total_pages})",
            min_value=1,
            max_value=total_pages,
            value=1,
            step=1,
            key="page_num",
        )
    with col_prev:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("◀ Prev", key="prev_btn") and page > 1:
            page -= 1
    with col_next:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Next ▶", key="next_btn") and page < total_pages:
            page += 1

    # Fetch page
    records, _ = get_orders_page(match, page=page, page_size=page_size)

    if records:
        df = pd.DataFrame(records)
        # Format dates
        if "order_date" in df.columns:
            df["order_date"] = pd.to_datetime(df["order_date"]).dt.strftime("%Y-%m-%d %H:%M")
        # Format currency
        for col in ["item_price", "discount", "delivery_fee", "total_amount"]:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: f"₹{x:,.2f}" if pd.notna(x) and x else "—")

        df_display = df.rename(columns=lambda c: c.replace("_", " ").title())
        st.dataframe(df_display, use_container_width=True, hide_index=True, height=420)

        # Export
        st.markdown("<br>", unsafe_allow_html=True)
        csv_bytes = export_orders_csv(match)
        st.download_button(
            label="⬇️ Export Filtered Results as CSV",
            data=csv_bytes,
            file_name="food_delivery_export.csv",
            mime="text/csv",
            key="export_btn",
        )
    else:
        st.info("ℹ️ No records found for the selected filters.")

# ══════════════════════════════════════════════════════════════════════════════
# Tab 2: Import Data
# ══════════════════════════════════════════════════════════════════════════════
with tab_import:
    section_header("Import CSV Dataset", "Upload a CSV file to import into MongoDB")

    st.markdown(
        """
        **Supported columns:** `order_id`, `order_date`, `customer_id`, `restaurant_name`,
        `city`, `food_category`, `item_name`, `quantity`, `item_price`, `discount`,
        `delivery_fee`, `total_amount`, `payment_method`, `order_status`,
        `delivery_time_minutes`, `customer_rating`

        **Required columns:** `order_id`, `order_date`, `restaurant_name`, `total_amount`
        """
    )

    uploaded = st.file_uploader(
        "Choose a CSV file",
        type=["csv"],
        key="csv_upload",
        help="Max recommended size: 50MB. Larger files may take several minutes.",
    )

    chunk_size = st.slider("Batch size (rows per chunk)", 100, 5000, 1000, 100, key="chunk_size_slider")

    if uploaded and st.button("🚀 Start Import", key="import_btn"):
        import tempfile, pathlib

        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".csv", dir=os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        ) as tmp:
            tmp.write(uploaded.getvalue())
            tmp_path = tmp.name

        progress_bar = st.progress(0, text="Starting import …")
        status_text = st.empty()

        def _progress(pct, msg):
            progress_bar.progress(min(pct, 1.0), text=msg)

        try:
            result = import_csv(tmp_path, chunk_size=chunk_size, progress_callback=_progress)
            st.success(
                f"✅ Import complete! "
                f"**{result['inserted']:,}** inserted • "
                f"**{result['updated']:,}** updated • "
                f"**{result['rejected']:,}** rejected • "
                f"took **{result['duration_seconds']}s**"
            )
            # Invalidate caches
            st.cache_data.clear()
        except Exception as exc:
            st.error(f"❌ Import failed: {exc}")
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    # Sample download
    sample_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "food_delivery_sample.csv"
    )
    if os.path.exists(sample_path):
        with open(sample_path, "rb") as f:
            st.download_button(
                "⬇️ Download Sample CSV",
                data=f.read(),
                file_name="food_delivery_sample.csv",
                mime="text/csv",
                key="sample_dl",
            )

# ══════════════════════════════════════════════════════════════════════════════
# Tab 3: Import History
# ══════════════════════════════════════════════════════════════════════════════
with tab_logs:
    section_header("Import History", "Recent data import operations")

    @st.cache_data(ttl=30, show_spinner=False)
    def _logs():
        return get_import_history(20)

    logs = _logs()
    if logs:
        df_logs = pd.DataFrame(logs)
        if "imported_at" in df_logs.columns:
            df_logs["imported_at"] = pd.to_datetime(df_logs["imported_at"]).dt.strftime("%Y-%m-%d %H:%M:%S")
        if "errors" in df_logs.columns:
            df_logs["error_count"] = df_logs["errors"].apply(lambda x: len(x) if isinstance(x, list) else 0)
            df_logs = df_logs.drop(columns=["errors"])
        df_logs.columns = [c.replace("_", " ").title() for c in df_logs.columns]
        st.dataframe(df_logs, use_container_width=True, hide_index=True)

        # Export logs
        csv_logs = export_summary_csv(logs)
        st.download_button(
            "⬇️ Export Import Logs",
            data=csv_logs,
            file_name="import_history.csv",
            mime="text/csv",
            key="export_logs",
        )
    else:
        st.info("ℹ️ No import history found. Import a dataset first.")
