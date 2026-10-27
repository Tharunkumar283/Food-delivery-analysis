"""
pages/1_Overview.py
Overview KPI dashboard with global filters.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from database.connection import ping
from analytics.aggregations import (
    get_overview_kpis,
    get_revenue_by_month,
    get_order_status_distribution,
    get_payment_distribution,
    get_orders_by_weekday,
    get_revenue_by_city,
)
from analytics.queries import get_filter_options
from utils.charts import (
    line_revenue_trend,
    donut_chart,
    bar_vertical,
    fmt_currency,
    fmt_number,
)
from utils.helpers import (
    sidebar_date_filter,
    sidebar_filter_select,
    kpi_card,
    section_header,
    safe_round,
)

st.set_page_config(page_title="Overview | Food Delivery Analytics", layout="wide")

# Inject global dark CSS (minimal repeat)
st.markdown(
    "<style>.stApp{background:linear-gradient(160deg,#0d1117 0%,#111827 100%);}</style>",
    unsafe_allow_html=True,
)

# ── Sidebar filters ────────────────────────────────────────────────────────────
st.sidebar.header("🔍 Filters")
start_dt, end_dt = sidebar_date_filter("overview")

if ping():
    opts = get_filter_options()
else:
    opts = {"cities": ["All"], "restaurants": ["All"]}

city = sidebar_filter_select(opts["cities"], "City", "ov_city")
restaurant = sidebar_filter_select(opts["restaurants"], "Restaurant", "ov_restaurant")

# ── Page header ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <h1 style="background:linear-gradient(135deg,#6C63FF,#a78bfa);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    font-size:30px;margin-bottom:4px;">📊 Overview Dashboard</h1>
    <p style="color:#8892a4;margin-top:0;">Key performance indicators and high-level trends</p>
    """,
    unsafe_allow_html=True,
)

if not ping():
    st.error("❌ MongoDB is not reachable. Please start your database and refresh.")
    st.stop()

# ── Fetch KPIs ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=120, show_spinner=False)
def _kpis(start, end, city, restaurant):
    return get_overview_kpis(start=start, end=end, city=city, restaurant=restaurant)

kpis = _kpis(start_dt, end_dt, city, restaurant)

# ── KPI cards ──────────────────────────────────────────────────────────────────
section_header("Key Metrics")
cols = st.columns(4)
kpi_card(cols[0], "Total Orders", fmt_number(kpis.get("total_orders", 0)), icon="📦")
kpi_card(cols[1], "Total Revenue", fmt_currency(kpis.get("total_revenue", 0)), icon="💰")
kpi_card(cols[2], "Avg Order Value", fmt_currency(kpis.get("avg_order_value", 0)), icon="🧾")
kpi_card(cols[3], "Cancellation Rate", f"{safe_round(kpis.get('cancellation_rate', 0))}%", icon="❌")

st.markdown("<br>", unsafe_allow_html=True)
cols2 = st.columns(4)
kpi_card(cols2[0], "Completed Orders", fmt_number(kpis.get("completed_orders", 0)), icon="✅")
kpi_card(cols2[1], "Cancelled Orders", fmt_number(kpis.get("cancelled_orders", 0)), icon="🚫")
kpi_card(cols2[2], "Avg Delivery Time", f"{safe_round(kpis.get('avg_delivery_time', 0))} min", icon="🚚")
kpi_card(cols2[3], "Avg Customer Rating", f"{safe_round(kpis.get('avg_rating', 0), 1)} / 5", icon="⭐")

st.markdown("<br>", unsafe_allow_html=True)

# ── Revenue trend ──────────────────────────────────────────────────────────────
section_header("Revenue Trends")

@st.cache_data(ttl=120, show_spinner=False)
def _monthly(start, end, city, restaurant):
    return get_revenue_by_month(start=start, end=end, city=city, restaurant=restaurant)

monthly_data = _monthly(start_dt, end_dt, city, restaurant)
st.plotly_chart(
    line_revenue_trend(monthly_data, "month", "📈 Monthly Revenue (Completed Orders)"),
    use_container_width=True,
    key="ov_monthly_revenue",
)

# ── Two column charts ──────────────────────────────────────────────────────────
col_l, col_r = st.columns(2)

@st.cache_data(ttl=120, show_spinner=False)
def _status(start, end, city, restaurant):
    return get_order_status_distribution(start=start, end=end, city=city, restaurant=restaurant)

@st.cache_data(ttl=120, show_spinner=False)
def _payment(start, end, city, restaurant):
    return get_payment_distribution(start=start, end=end, city=city, restaurant=restaurant)

with col_l:
    status_data = _status(start_dt, end_dt, city, restaurant)
    st.plotly_chart(
        donut_chart(status_data, "status", "count", "🟢 Order Status Distribution"),
        use_container_width=True,
        key="ov_status_donut",
    )

with col_r:
    pay_data = _payment(start_dt, end_dt, city, restaurant)
    st.plotly_chart(
        donut_chart(pay_data, "payment_method", "count", "💳 Payment Method Distribution"),
        use_container_width=True,
        key="ov_payment_donut",
    )

# ── Revenue by city ────────────────────────────────────────────────────────────
section_header("Revenue by City")

@st.cache_data(ttl=120, show_spinner=False)
def _city_rev(start, end):
    return get_revenue_by_city(start=start, end=end)

city_data = _city_rev(start_dt, end_dt)
st.plotly_chart(
    bar_vertical(city_data, "city", "revenue", "🏙️ Revenue by City"),
    use_container_width=True,
    key="ov_city_revenue",
)

# ── Weekday activity ───────────────────────────────────────────────────────────
section_header("Orders by Weekday")

@st.cache_data(ttl=120, show_spinner=False)
def _weekday(start, end):
    return get_orders_by_weekday(start=start, end=end)

wd_data = _weekday(start_dt, end_dt)
st.plotly_chart(
    bar_vertical(wd_data, "weekday", "orders", "📅 Orders by Day of Week", color="#34d399"),
    use_container_width=True,
    key="ov_weekday_orders",
)
