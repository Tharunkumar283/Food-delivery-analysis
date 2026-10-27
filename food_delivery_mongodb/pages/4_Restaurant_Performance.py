"""
pages/4_Restaurant_Performance.py
Restaurant-level performance metrics: revenue, orders, delivery, ratings, cancellations.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from database.connection import ping
from analytics.aggregations import (
    get_top_restaurants_by_revenue,
    get_top_restaurants_by_orders,
    get_restaurant_performance,
    get_avg_delivery_by_restaurant,
    get_rating_by_restaurant,
)
from analytics.queries import get_filter_options
from utils.charts import bar_horizontal, bar_vertical, scatter_plot, fmt_currency
from utils.helpers import (
    sidebar_date_filter,
    sidebar_filter_select,
    section_header,
    no_data_message,
    safe_round,
)

st.set_page_config(page_title="Restaurant Performance | Food Delivery Analytics", layout="wide")
st.markdown(
    "<style>.stApp{background:linear-gradient(160deg,#0d1117 0%,#111827 100%);}</style>",
    unsafe_allow_html=True,
)

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.header("🔍 Filters")
start_dt, end_dt = sidebar_date_filter("rest")

if ping():
    opts = get_filter_options()
else:
    opts = {"cities": ["All"], "categories": ["All"]}

city = sidebar_filter_select(opts["cities"], "City", "rp_city")
category = sidebar_filter_select(opts.get("categories", ["All"]), "Food Category", "rp_cat")

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <h1 style="background:linear-gradient(135deg,#fbbf24,#f59e0b);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    font-size:30px;margin-bottom:4px;">🏪 Restaurant Performance</h1>
    <p style="color:#8892a4;margin-top:0;">Comparative analysis across restaurants</p>
    """,
    unsafe_allow_html=True,
)

if not ping():
    st.error("❌ MongoDB is not reachable.")
    st.stop()

kwargs = dict(start=start_dt, end=end_dt, city=city, food_category=category)

# ── Top by Revenue vs Orders ───────────────────────────────────────────────────
col_l, col_r = st.columns(2)

@st.cache_data(ttl=120, show_spinner=False)
def _top_rev(start, end, city, category):
    return get_top_restaurants_by_revenue(10, start=start, end=end, city=city, food_category=category)

@st.cache_data(ttl=120, show_spinner=False)
def _top_orders(start, end, city, category):
    return get_top_restaurants_by_orders(10, start=start, end=end, city=city, food_category=category)

with col_l:
    section_header("Top 10 by Revenue")
    rev_data = _top_rev(start_dt, end_dt, city, category)
    st.plotly_chart(
        bar_horizontal(rev_data, "revenue", "restaurant", "💰 Top 10 Restaurants by Revenue", height=450),
        use_container_width=True,
    )

with col_r:
    section_header("Top 10 by Order Volume")
    ord_data = _top_orders(start_dt, end_dt, city, category)
    st.plotly_chart(
        bar_horizontal(ord_data, "orders", "restaurant", "📦 Top 10 Restaurants by Orders", color="#34d399", height=450),
        use_container_width=True,
    )

# ── Delivery time by restaurant ────────────────────────────────────────────────
section_header("Avg Delivery Time by Restaurant (Top 15 Fastest)")

@st.cache_data(ttl=120, show_spinner=False)
def _delivery_rest(start, end, city):
    return get_avg_delivery_by_restaurant(15, start=start, end=end, city=city)

del_data = _delivery_rest(start_dt, end_dt, city)
if del_data:
    st.plotly_chart(
        bar_horizontal(del_data, "avg_delivery", "restaurant", "🚚 Avg Delivery Time (min)", color="#60a5fa", height=450),
        use_container_width=True,
    )
else:
    no_data_message("No delivery time data for the selected filters.")

# ── Ratings comparison ─────────────────────────────────────────────────────────
section_header("Customer Ratings by Restaurant (min 5 orders)")

@st.cache_data(ttl=120, show_spinner=False)
def _ratings_rest(start, end, city):
    return get_rating_by_restaurant(10, start=start, end=end, city=city)

rating_data = _ratings_rest(start_dt, end_dt, city)
if rating_data:
    st.plotly_chart(
        bar_horizontal(rating_data, "avg_rating", "restaurant", "⭐ Avg Rating by Restaurant", color="#a78bfa", height=400),
        use_container_width=True,
    )

# ── Full performance table ─────────────────────────────────────────────────────
section_header("Full Restaurant Performance Table")

@st.cache_data(ttl=120, show_spinner=False)
def _perf_table(start, end, city, category):
    return get_restaurant_performance(start=start, end=end, city=city, food_category=category)

perf_data = _perf_table(start_dt, end_dt, city, category)
if perf_data:
    df = pd.DataFrame(perf_data)
    # Format columns
    if "revenue" in df.columns:
        df["revenue"] = df["revenue"].apply(fmt_currency)
    if "avg_delivery" in df.columns:
        df["avg_delivery"] = df["avg_delivery"].apply(lambda x: f"{safe_round(x)} min" if x else "N/A")
    if "avg_rating" in df.columns:
        df["avg_rating"] = df["avg_rating"].apply(lambda x: f"{safe_round(x, 1)}" if x else "N/A")
    if "cancellation_rate" in df.columns:
        df["cancellation_rate"] = df["cancellation_rate"].apply(lambda x: f"{safe_round(x)}%")

    df.columns = [c.replace("_", " ").title() for c in df.columns]
    st.dataframe(df, use_container_width=True, hide_index=True, height=400)
else:
    no_data_message("No restaurant data for the selected filters.")
