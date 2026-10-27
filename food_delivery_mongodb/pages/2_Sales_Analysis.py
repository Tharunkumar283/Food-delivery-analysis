"""
pages/2_Sales_Analysis.py
Revenue and sales deep-dive with daily/monthly/weekly trends.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from database.connection import ping
from analytics.aggregations import (
    get_revenue_by_day,
    get_revenue_by_month,
    get_revenue_by_week,
    get_revenue_by_category,
    get_revenue_by_city,
    get_top_restaurants_by_revenue,
)
from analytics.queries import get_filter_options
from utils.charts import (
    line_revenue_trend,
    bar_horizontal,
    bar_vertical,
    donut_chart,
    fmt_currency,
)
from utils.helpers import (
    sidebar_date_filter,
    sidebar_filter_select,
    section_header,
    no_data_message,
)
import pandas as pd

st.set_page_config(page_title="Sales Analysis | Food Delivery Analytics", layout="wide")
st.markdown(
    "<style>.stApp{background:linear-gradient(160deg,#0d1117 0%,#111827 100%);}</style>",
    unsafe_allow_html=True,
)

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.header("🔍 Filters")
start_dt, end_dt = sidebar_date_filter("sales")

if ping():
    opts = get_filter_options()
else:
    opts = {"cities": ["All"], "restaurants": ["All"], "categories": ["All"]}

city = sidebar_filter_select(opts["cities"], "City", "sa_city")
category = sidebar_filter_select(opts.get("categories", ["All"]), "Food Category", "sa_cat")

# ── Page header ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <h1 style="background:linear-gradient(135deg,#34d399,#059669);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    font-size:30px;margin-bottom:4px;">💰 Sales & Revenue Analysis</h1>
    <p style="color:#8892a4;margin-top:0;">Daily, monthly, and category-level revenue breakdown</p>
    """,
    unsafe_allow_html=True,
)

if not ping():
    st.error("❌ MongoDB is not reachable.")
    st.stop()

kwargs = dict(start=start_dt, end=end_dt, city=city, food_category=category)

# ── Trend granularity selector ─────────────────────────────────────────────────
section_header("Revenue Trends")
granularity = st.radio(
    "Granularity",
    ["Daily", "Weekly", "Monthly"],
    horizontal=True,
    key="granularity",
)

@st.cache_data(ttl=120, show_spinner=False)
def _trend(gran, start, end, city, category):
    if gran == "Daily":
        return get_revenue_by_day(start=start, end=end, city=city, food_category=category), "date"
    if gran == "Weekly":
        return get_revenue_by_week(start=start, end=end, city=city, food_category=category), "week"
    return get_revenue_by_month(start=start, end=end, city=city, food_category=category), "month"

trend_data, x_field = _trend(granularity, start_dt, end_dt, city, category)
st.plotly_chart(
    line_revenue_trend(trend_data, x_field, f"📈 {granularity} Revenue (Completed Orders)"),
    use_container_width=True,
    key="sa_trend",
)

# ── Revenue by Category ────────────────────────────────────────────────────────
col_l, col_r = st.columns(2)

@st.cache_data(ttl=120, show_spinner=False)
def _cat_rev(start, end, city):
    return get_revenue_by_category(start=start, end=end, city=city)

with col_l:
    section_header("Revenue by Food Category")
    cat_data = _cat_rev(start_dt, end_dt, city)
    st.plotly_chart(
        bar_horizontal(cat_data, "revenue", "category", "🍔 Revenue by Category"),
        use_container_width=True,
        key="sa_cat_bar",
    )

with col_r:
    section_header("Orders by Food Category")
    st.plotly_chart(
        donut_chart(cat_data, "category", "orders", "🍕 Order Share by Category"),
        use_container_width=True,
        key="sa_cat_donut",
    )

# ── Revenue by City ────────────────────────────────────────────────────────────
section_header("Revenue by City")

@st.cache_data(ttl=120, show_spinner=False)
def _city_rev(start, end, category):
    return get_revenue_by_city(start=start, end=end, food_category=category)

city_data = _city_rev(start_dt, end_dt, category)
st.plotly_chart(
    bar_vertical(city_data, "city", "revenue", "🏙️ Revenue by City", color="#f472b6"),
    use_container_width=True,
    key="sa_city_revenue",
)

# ── Top 10 Restaurants by Revenue ─────────────────────────────────────────────
section_header("Top 10 Restaurants by Revenue")

@st.cache_data(ttl=120, show_spinner=False)
def _top_rest(start, end, city):
    return get_top_restaurants_by_revenue(10, start=start, end=end, city=city)

rest_data = _top_rest(start_dt, end_dt, city)
if rest_data:
    st.plotly_chart(
        bar_horizontal(rest_data, "revenue", "restaurant", "🏪 Top 10 Restaurants by Revenue", height=450),
        use_container_width=True,
        key="sa_top_rest",
    )
    # Table view
    df = pd.DataFrame(rest_data)
    df["revenue"] = df["revenue"].apply(fmt_currency)
    df.columns = [c.replace("_", " ").title() for c in df.columns]
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    no_data_message("No restaurant data for the selected filters.")
