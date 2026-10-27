"""
pages/5_Delivery_Analysis.py
Delivery performance analysis: time distribution, city comparison, status breakdown.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database.connection import ping
from analytics.aggregations import (
    get_delivery_time_distribution,
    get_avg_delivery_by_city,
    get_avg_delivery_by_restaurant,
    get_order_status_distribution,
    get_overview_kpis,
)
from analytics.queries import get_filter_options
from utils.charts import bar_horizontal, bar_vertical, donut_chart, fmt_number
from utils.helpers import (
    sidebar_date_filter,
    sidebar_filter_select,
    section_header,
    kpi_card,
    safe_round,
    no_data_message,
)

st.set_page_config(page_title="Delivery Analysis | Food Delivery Analytics", layout="wide")
st.markdown(
    "<style>.stApp{background:linear-gradient(160deg,#0d1117 0%,#111827 100%);}</style>",
    unsafe_allow_html=True,
)

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.header("🔍 Filters")
start_dt, end_dt = sidebar_date_filter("delivery")

if ping():
    opts = get_filter_options()
else:
    opts = {"cities": ["All"], "statuses": ["All"]}

city = sidebar_filter_select(opts["cities"], "City", "da_city")
status = sidebar_filter_select(opts.get("statuses", ["All"]), "Order Status", "da_status")

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <h1 style="background:linear-gradient(135deg,#60a5fa,#3b82f6);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    font-size:30px;margin-bottom:4px;">🚚 Delivery Performance</h1>
    <p style="color:#8892a4;margin-top:0;">Delivery time analysis, city comparison, and order status breakdown</p>
    """,
    unsafe_allow_html=True,
)

if not ping():
    st.error("❌ MongoDB is not reachable.")
    st.stop()

kwargs = dict(start=start_dt, end=end_dt, city=city, order_status=status)

# ── KPIs ───────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=120, show_spinner=False)
def _kpis(start, end, city, status):
    return get_overview_kpis(start=start, end=end, city=city, order_status=status)

kpis = _kpis(start_dt, end_dt, city, status)
cols = st.columns(4)
kpi_card(cols[0], "Total Orders", fmt_number(kpis.get("total_orders", 0)), icon="📦")
kpi_card(cols[1], "Avg Delivery Time", f"{safe_round(kpis.get('avg_delivery_time', 0))} min", icon="⏱️")
kpi_card(cols[2], "Completed Orders", fmt_number(kpis.get("completed_orders", 0)), icon="✅")
kpi_card(cols[3], "Cancellation Rate", f"{safe_round(kpis.get('cancellation_rate', 0))}%", icon="❌")

st.markdown("<br>", unsafe_allow_html=True)

# ── Delivery time distribution ─────────────────────────────────────────────────
section_header("Delivery Time Distribution")

@st.cache_data(ttl=120, show_spinner=False)
def _dist(start, end, city):
    return get_delivery_time_distribution(start=start, end=end, city=city)

dist_data = _dist(start_dt, end_dt, city)
if dist_data:
    labels = []
    counts = []
    for bucket in dist_data:
        key = bucket.get("_id")
        if key == "300+":
            labels.append("300+ min")
        else:
            labels.append(f"{key} min")
        counts.append(bucket.get("count", 0))

    fig = go.Figure(go.Bar(
        x=labels, y=counts,
        marker=dict(
            color=counts,
            colorscale="Plasma",
            line=dict(width=0),
        ),
    ))
    fig.update_layout(
        title=dict(text="🕒 Delivery Time Buckets", font=dict(size=15, color="#e0e0e0")),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#cccccc"), height=380,
        xaxis=dict(title="Delivery Time (minutes)", showgrid=False, linecolor="#333"),
        yaxis=dict(title="Number of Orders", showgrid=True, gridcolor="#333"),
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    no_data_message("No delivery time data available (field may be missing in the dataset).")

# ── City delivery comparison ───────────────────────────────────────────────────
section_header("Avg Delivery Time by City")

@st.cache_data(ttl=120, show_spinner=False)
def _city_del(start, end):
    return get_avg_delivery_by_city(start=start, end=end)

city_del = _city_del(start_dt, end_dt)
if city_del:
    st.plotly_chart(
        bar_horizontal(city_del, "avg_delivery", "city", "🏙️ Average Delivery Time by City (min)", color="#60a5fa", height=400),
        use_container_width=True,
    )
else:
    no_data_message("No city delivery data available.")

# ── Order status distribution ──────────────────────────────────────────────────
col_l, col_r = st.columns(2)

@st.cache_data(ttl=120, show_spinner=False)
def _status_dist(start, end, city):
    return get_order_status_distribution(start=start, end=end, city=city)

with col_l:
    section_header("Order Status Distribution")
    status_data = _status_dist(start_dt, end_dt, city)
    st.plotly_chart(
        donut_chart(status_data, "status", "count", "🔄 Order Status Breakdown"),
        use_container_width=True,
    )

# ── Restaurant delivery table ──────────────────────────────────────────────────
@st.cache_data(ttl=120, show_spinner=False)
def _rest_del(start, end, city):
    return get_avg_delivery_by_restaurant(15, start=start, end=end, city=city)

with col_r:
    section_header("Fastest Delivery Restaurants")
    rd_data = _rest_del(start_dt, end_dt, city)
    if rd_data:
        df = pd.DataFrame(rd_data)
        df["avg_delivery"] = df["avg_delivery"].apply(lambda x: f"{safe_round(x)} min")
        df.columns = [c.replace("_", " ").title() for c in df.columns]
        st.dataframe(df, use_container_width=True, hide_index=True, height=380)
    else:
        no_data_message("No restaurant delivery data.")
