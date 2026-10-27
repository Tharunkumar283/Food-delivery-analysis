"""
pages/3_Customer_Analysis.py
Customer and order behaviour: ordering hours, weekdays, payments, ratings.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from database.connection import ping
from analytics.aggregations import (
    get_orders_by_hour,
    get_orders_by_weekday,
    get_payment_distribution,
    get_rating_distribution,
    get_heatmap_data,
    get_overview_kpis,
)
from analytics.queries import get_filter_options
from utils.charts import (
    bar_vertical,
    donut_chart,
    heatmap_day_hour,
    histogram,
    fmt_number,
)
from utils.helpers import (
    sidebar_date_filter,
    sidebar_filter_select,
    section_header,
    kpi_card,
    safe_round,
)
import pandas as pd

st.set_page_config(page_title="Customer Analysis | Food Delivery Analytics", layout="wide")
st.markdown(
    "<style>.stApp{background:linear-gradient(160deg,#0d1117 0%,#111827 100%);}</style>",
    unsafe_allow_html=True,
)

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.header("🔍 Filters")
start_dt, end_dt = sidebar_date_filter("customer")

if ping():
    opts = get_filter_options()
else:
    opts = {"cities": ["All"], "payments": ["All"], "statuses": ["All"]}

city = sidebar_filter_select(opts["cities"], "City", "cu_city")
status = sidebar_filter_select(opts.get("statuses", ["All"]), "Order Status", "cu_status")
payment = sidebar_filter_select(opts.get("payments", ["All"]), "Payment Method", "cu_payment")

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <h1 style="background:linear-gradient(135deg,#f472b6,#ec4899);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    font-size:30px;margin-bottom:4px;">👥 Customer & Order Analysis</h1>
    <p style="color:#8892a4;margin-top:0;">Order timing, payment preferences, and customer ratings</p>
    """,
    unsafe_allow_html=True,
)

if not ping():
    st.error("❌ MongoDB is not reachable.")
    st.stop()

kwargs = dict(start=start_dt, end=end_dt, city=city, order_status=status, payment_method=payment)

# ── Mini KPIs ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=120, show_spinner=False)
def _kpis(start, end, city, status, payment):
    return get_overview_kpis(start=start, end=end, city=city, order_status=status, payment_method=payment)

kpis = _kpis(start_dt, end_dt, city, status, payment)
cols = st.columns(4)
kpi_card(cols[0], "Total Orders", fmt_number(kpis.get("total_orders", 0)), icon="📦")
kpi_card(cols[1], "Avg Rating", f"{safe_round(kpis.get('avg_rating', 0), 1)} ⭐", icon="⭐")
kpi_card(cols[2], "Avg Order Value", f"₹{safe_round(kpis.get('avg_order_value', 0)):,.0f}", icon="🧾")
kpi_card(cols[3], "Cancellation Rate", f"{safe_round(kpis.get('cancellation_rate', 0))}%", icon="❌")

st.markdown("<br>", unsafe_allow_html=True)

# ── Order heatmap ──────────────────────────────────────────────────────────────
section_header("Order Activity Heatmap", "Orders by day of week and hour of day")

@st.cache_data(ttl=120, show_spinner=False)
def _heatmap(start, end, city):
    return get_heatmap_data(start=start, end=end, city=city)

hm_data = _heatmap(start_dt, end_dt, city)
st.plotly_chart(heatmap_day_hour(hm_data), use_container_width=True)

# ── Hourly & Weekday charts ───────────────────────────────────────────────────
col_l, col_r = st.columns(2)

@st.cache_data(ttl=120, show_spinner=False)
def _hourly(start, end, city):
    return get_orders_by_hour(start=start, end=end, city=city)

@st.cache_data(ttl=120, show_spinner=False)
def _weekday(start, end, city):
    return get_orders_by_weekday(start=start, end=end, city=city)

with col_l:
    section_header("Peak Ordering Hours")
    hour_data = _hourly(start_dt, end_dt, city)
    if hour_data:
        df = pd.DataFrame(hour_data)
        df["hour_label"] = df["hour"].apply(lambda h: f"{h:02d}:00")
        import plotly.express as px
        fig = px.bar(
            df, x="hour_label", y="orders",
            color="orders",
            color_continuous_scale="Plasma",
            labels={"hour_label": "Hour", "orders": "Orders"},
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#cccccc"), height=380,
            title=dict(text="⏰ Orders by Hour of Day", font=dict(size=15, color="#e0e0e0")),
            coloraxis_showscale=False,
        )
        fig.update_xaxes(showgrid=False, linecolor="#333")
        fig.update_yaxes(showgrid=True, gridcolor="#333")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hourly data available.")

with col_r:
    section_header("Busiest Weekdays")
    wd_data = _weekday(start_dt, end_dt, city)
    st.plotly_chart(
        bar_vertical(wd_data, "weekday", "orders", "📅 Orders by Weekday", color="#a78bfa"),
        use_container_width=True,
    )

# ── Payment distribution ───────────────────────────────────────────────────────
col_l2, col_r2 = st.columns(2)

@st.cache_data(ttl=120, show_spinner=False)
def _payment_dist(start, end, city):
    return get_payment_distribution(start=start, end=end, city=city)

with col_l2:
    section_header("Payment Method Distribution")
    pay_data = _payment_dist(start_dt, end_dt, city)
    st.plotly_chart(
        donut_chart(pay_data, "payment_method", "count", "💳 Payment Methods"),
        use_container_width=True,
    )

# ── Rating distribution ────────────────────────────────────────────────────────
@st.cache_data(ttl=120, show_spinner=False)
def _ratings(start, end, city):
    return get_rating_distribution(start=start, end=end, city=city)

with col_r2:
    section_header("Customer Rating Distribution")
    rating_data = _ratings(start_dt, end_dt, city)
    if rating_data:
        df_r = pd.DataFrame(rating_data)
        df_r["rating_label"] = df_r["rating"].apply(lambda x: f"{'⭐'*int(x)} ({int(x)})")
        st.plotly_chart(
            bar_vertical(
                df_r.rename(columns={"rating_label": "rating_str"}),
                "rating_str", "count",
                "⭐ Customer Rating Distribution",
                color="#fbbf24",
                height=380,
            ),
            use_container_width=True,
        )
    else:
        st.info("No rating data available.")
