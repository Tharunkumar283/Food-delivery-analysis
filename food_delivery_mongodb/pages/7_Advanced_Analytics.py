"""
pages/7_Advanced_Analytics.py
Advanced analytics dashboard with three analysis tabs:
  - Customer Segmentation (RFM)
  - Repeat Customer / Loyalty Analysis
  - Discount Impact Analysis
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database.connection import ping
from analytics.advanced import (
    get_rfm_segments,
    get_segment_summary,
    get_repeat_customer_stats,
    get_order_frequency_distribution,
    get_top_loyal_customers,
    get_customer_retention_by_month,
    get_discount_overview,
    get_discount_bands,
    get_discount_trend_by_month,
    get_discount_by_category,
)
from analytics.queries import get_filter_options
from utils.charts import fmt_currency, fmt_number, donut_chart, bar_horizontal, bar_vertical
from utils.helpers import (
    sidebar_date_filter,
    sidebar_filter_select,
    section_header,
    kpi_card,
    safe_round,
    no_data_message,
)

st.set_page_config(
    page_title="Advanced Analytics | Food Delivery Analytics",
    layout="wide",
)

# ── Global dark CSS ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    .stApp {
        background: linear-gradient(160deg, #0d1117 0%, #111827 100%);
        color: #e0e0e0;
    }

    /* Segment badge colours */
    .seg-champions { background: linear-gradient(135deg, #fbbf24, #f59e0b); color: #000; }
    .seg-loyal { background: linear-gradient(135deg, #34d399, #059669); color: #000; }
    .seg-potential { background: linear-gradient(135deg, #60a5fa, #3b82f6); color: #fff; }
    .seg-atrisk { background: linear-gradient(135deg, #f472b6, #ec4899); color: #fff; }
    .seg-hibernating { background: linear-gradient(135deg, #a78bfa, #8b5cf6); color: #fff; }
    .seg-lost { background: linear-gradient(135deg, #6b7280, #4b5563); color: #fff; }
    .seg-badge {
        display: inline-block; padding: 4px 14px; border-radius: 20px;
        font-size: 13px; font-weight: 600; letter-spacing: 0.5px;
    }

    /* Comparison cards */
    .compare-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #1e2436 100%);
        border: 1px solid #2e3850;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    .compare-card h4 { color: #8892a4; font-size: 13px; text-transform: uppercase; margin: 0 0 8px 0; }
    .compare-card .val { font-size: 28px; font-weight: 700; color: #fff; }
    .compare-card .sub { font-size: 12px; color: #6b7280; margin-top: 4px; }

    /* Insight box */
    .insight-box {
        background: linear-gradient(135deg, #1e2130, #252d3d);
        border-left: 4px solid #6C63FF;
        border-radius: 8px;
        padding: 16px 20px;
        margin: 12px 0;
        font-size: 14px;
        color: #c9d1d9;
        line-height: 1.6;
    }
    .insight-box strong { color: #e0e0e0; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar ─────────────────────────────────────────────────────────────────────
st.sidebar.header("🔍 Filters")
start_dt, end_dt = sidebar_date_filter("adv")

if ping():
    opts = get_filter_options()
else:
    opts = {"cities": ["All"], "categories": ["All"]}

city = sidebar_filter_select(opts["cities"], "City", "adv_city")
category = sidebar_filter_select(opts.get("categories", ["All"]), "Food Category", "adv_cat")

# ── Header ──────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <h1 style="background:linear-gradient(135deg,#6C63FF,#a78bfa,#ec4899);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    font-size:30px;margin-bottom:4px;">🧠 Advanced Analytics</h1>
    <p style="color:#8892a4;margin-top:0;">
        Customer segmentation, loyalty analysis, and discount impact insights
    </p>
    """,
    unsafe_allow_html=True,
)

if not ping():
    st.error("❌ MongoDB is not reachable. Please start your database and refresh.")
    st.stop()

kwargs = dict(start=start_dt, end=end_dt, city=city, food_category=category)

# ── Tabs ────────────────────────────────────────────────────────────────────────
tab_rfm, tab_loyalty, tab_discount = st.tabs([
    "👥 Customer Segmentation (RFM)",
    "🔄 Repeat Customer Analysis",
    "💸 Discount Impact",
])


# ═══════════════════════════════════════════════════════════════════════════════
#  TAB 1: RFM Customer Segmentation
# ═══════════════════════════════════════════════════════════════════════════════
with tab_rfm:
    section_header(
        "RFM Customer Segmentation",
        "Recency · Frequency · Monetary analysis to identify high-value customer segments",
    )

    # ── Segment summary KPIs ────────────────────────────────────────────────────
    @st.cache_data(ttl=120, show_spinner=False)
    def _seg_summary(start, end, city, category):
        return get_segment_summary(start=start, end=end, city=city, food_category=category)

    seg_data = _seg_summary(start_dt, end_dt, city, category)

    if not seg_data:
        no_data_message("No customer data available for segmentation. Ensure customer_id is present in your dataset.")
    else:
        # Segment distribution donut
        col_donut, col_table = st.columns([1, 1.5])

        with col_donut:
            seg_colors = {
                "Champions": "#fbbf24",
                "Loyal": "#34d399",
                "Potential": "#60a5fa",
                "At Risk": "#f472b6",
                "Hibernating": "#a78bfa",
                "Lost": "#6b7280",
            }
            fig = px.pie(
                pd.DataFrame(seg_data),
                names="segment",
                values="customers",
                hole=0.5,
                color="segment",
                color_discrete_map=seg_colors,
            )
            fig.update_traces(
                textposition="inside",
                textinfo="percent+label",
                hovertemplate="<b>%{label}</b><br>Customers: %{value:,}<br>Share: %{percent}",
            )
            fig.update_layout(
                title=dict(text="🎯 Customer Segment Distribution", font=dict(size=16, color="#e0e0e0")),
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#cccccc"),
                height=420,
                margin=dict(l=20, r=20, t=50, b=20),
                legend=dict(bgcolor="rgba(0,0,0,0.3)"),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_table:
            st.markdown("#### Segment Performance Table")
            df_seg = pd.DataFrame(seg_data)
            df_seg["total_revenue"] = df_seg["total_revenue"].apply(fmt_currency)
            df_seg["avg_monetary"] = df_seg["avg_monetary"].apply(fmt_currency)
            df_seg.columns = [c.replace("_", " ").title() for c in df_seg.columns]
            st.dataframe(df_seg, use_container_width=True, hide_index=True, height=380)

        # ── Segment insight box ─────────────────────────────────────────────
        top_seg = seg_data[0] if seg_data else {}
        total_cust = sum(s["customers"] for s in seg_data)
        champs = next((s for s in seg_data if s["segment"] == "Champions"), None)
        at_risk = next((s for s in seg_data if s["segment"] == "At Risk"), None)

        insights = []
        if champs:
            pct = round(champs["customers"] / max(total_cust, 1) * 100, 1)
            insights.append(
                f"🏆 <strong>Champions</strong> ({pct}% of customers) generate "
                f"<strong>{fmt_currency(champs['total_revenue'])}</strong> in revenue."
            )
        if at_risk:
            pct = round(at_risk["customers"] / max(total_cust, 1) * 100, 1)
            insights.append(
                f"⚠️ <strong>At Risk</strong> customers ({pct}%) haven't ordered recently "
                f"but were previously active — consider re-engagement campaigns."
            )

        if insights:
            st.markdown(
                '<div class="insight-box">' + "<br>".join(insights) + "</div>",
                unsafe_allow_html=True,
            )

        # ── RFM scatter: Frequency vs Monetary, coloured by segment ─────────
        section_header("RFM Scatter Plot", "Each dot is a customer — hover for details")

        @st.cache_data(ttl=120, show_spinner=False)
        def _rfm_full(start, end, city, category):
            return get_rfm_segments(start=start, end=end, city=city, food_category=category)

        rfm_full = _rfm_full(start_dt, end_dt, city, category)
        if rfm_full:
            df_rfm = pd.DataFrame(rfm_full)
            fig_scatter = px.scatter(
                df_rfm,
                x="frequency",
                y="monetary",
                color="segment",
                size="recency_days",
                size_max=18,
                color_discrete_map=seg_colors,
                hover_data=["customer_id", "recency_days", "avg_rating", "rfm_score"],
                labels={"frequency": "Order Frequency", "monetary": "Total Spend (₹)"},
            )
            fig_scatter.update_layout(
                title=dict(text="📊 Customer RFM Scatter — Frequency vs Monetary", font=dict(size=16, color="#e0e0e0")),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#cccccc"),
                height=480,
                legend=dict(bgcolor="rgba(0,0,0,0.3)", bordercolor="#444"),
                hoverlabel=dict(bgcolor="#1e2130", font_color="#ffffff"),
            )
            fig_scatter.update_xaxes(showgrid=True, gridcolor="#333", linecolor="#333")
            fig_scatter.update_yaxes(showgrid=True, gridcolor="#333", linecolor="#333")
            st.plotly_chart(fig_scatter, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  TAB 2: Repeat Customer / Loyalty Analysis
# ═══════════════════════════════════════════════════════════════════════════════
with tab_loyalty:
    section_header(
        "Repeat Customer Analysis",
        "Customer loyalty metrics, return rates, and cohort behaviour",
    )

    @st.cache_data(ttl=120, show_spinner=False)
    def _repeat_stats(start, end, city, category):
        return get_repeat_customer_stats(start=start, end=end, city=city, food_category=category)

    stats = _repeat_stats(start_dt, end_dt, city, category)

    if stats.get("total_customers", 0) == 0:
        no_data_message("No customer data available. Ensure customer_id is present in your dataset.")
    else:
        # ── KPI row ────────────────────────────────────────────────────────
        cols = st.columns(4)
        kpi_card(cols[0], "Unique Customers", fmt_number(stats.get("total_customers", 0)), icon="👥")
        kpi_card(cols[1], "Repeat Rate", f"{safe_round(stats.get('repeat_rate', 0))}%", icon="🔄")
        kpi_card(
            cols[2], "Repeat Revenue Share",
            f"{safe_round(stats.get('repeat_revenue_share', 0))}%",
            icon="💰",
        )
        kpi_card(
            cols[3], "Avg Orders / Customer",
            f"{safe_round(stats.get('avg_orders_per_customer', 0), 1)}",
            icon="📊",
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── One-time vs Repeat comparison cards ────────────────────────────
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown(
                f"""
                <div class="compare-card">
                    <h4>One-Time Customers</h4>
                    <div class="val">{stats.get('one_time', 0):,}</div>
                    <div class="sub">{round(100 - stats.get('repeat_rate', 0), 1)}% of total</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_b:
            st.markdown(
                f"""
                <div class="compare-card">
                    <h4>Repeat Customers</h4>
                    <div class="val" style="color:#34d399;">{stats.get('repeat', 0):,}</div>
                    <div class="sub">{safe_round(stats.get('repeat_rate', 0))}% of total</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_c:
            st.markdown(
                f"""
                <div class="compare-card">
                    <h4>Most Orders by 1 Customer</h4>
                    <div class="val" style="color:#fbbf24;">{stats.get('max_orders', 0)}</div>
                    <div class="sub">Highest individual order count</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Order frequency distribution ───────────────────────────────────
        col_freq, col_ret = st.columns(2)

        @st.cache_data(ttl=120, show_spinner=False)
        def _freq_dist(start, end, city, category):
            return get_order_frequency_distribution(start=start, end=end, city=city, food_category=category)

        with col_freq:
            section_header("Order Frequency Distribution")
            freq_data = _freq_dist(start_dt, end_dt, city, category)
            if freq_data:
                df_freq = pd.DataFrame(freq_data)
                fig_freq = px.bar(
                    df_freq,
                    x="order_count",
                    y="customers",
                    color="customers",
                    color_continuous_scale="Plasma",
                    labels={"order_count": "Number of Orders", "customers": "Customers"},
                )
                fig_freq.update_layout(
                    title=dict(text="📊 Customers by Order Count", font=dict(size=15, color="#e0e0e0")),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#cccccc"), height=380,
                    coloraxis_showscale=False,
                )
                fig_freq.update_xaxes(showgrid=False, linecolor="#333", dtick=1)
                fig_freq.update_yaxes(showgrid=True, gridcolor="#333")
                st.plotly_chart(fig_freq, use_container_width=True)
            else:
                no_data_message("No frequency data.")

        # ── Monthly new vs returning ───────────────────────────────────────
        @st.cache_data(ttl=120, show_spinner=False)
        def _retention(start, end, city, category):
            return get_customer_retention_by_month(start=start, end=end, city=city, food_category=category)

        with col_ret:
            section_header("Monthly New vs Returning Customers")
            ret_data = _retention(start_dt, end_dt, city, category)
            if ret_data:
                df_ret = pd.DataFrame(ret_data)
                fig_ret = go.Figure()
                fig_ret.add_trace(go.Bar(
                    name="New Customers", x=df_ret["month"], y=df_ret["new_customers"],
                    marker_color="#60a5fa",
                ))
                fig_ret.add_trace(go.Bar(
                    name="Returning Customers", x=df_ret["month"], y=df_ret["returning_customers"],
                    marker_color="#34d399",
                ))
                fig_ret.update_layout(
                    barmode="stack",
                    title=dict(text="📈 New vs Returning Customers", font=dict(size=15, color="#e0e0e0")),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#cccccc"), height=380,
                    legend=dict(bgcolor="rgba(0,0,0,0.3)", bordercolor="#444"),
                    xaxis=dict(showgrid=False, linecolor="#333"),
                    yaxis=dict(showgrid=True, gridcolor="#333"),
                )
                st.plotly_chart(fig_ret, use_container_width=True)
            else:
                no_data_message("No retention data.")

        # ── Loyalty insight ────────────────────────────────────────────────
        repeat_rate = stats.get("repeat_rate", 0)
        rev_share = stats.get("repeat_revenue_share", 0)
        insight_lines = []
        if repeat_rate > 0:
            insight_lines.append(
                f"🔄 <strong>{safe_round(repeat_rate)}%</strong> of customers are repeat buyers, "
                f"contributing <strong>{safe_round(rev_share)}%</strong> of total revenue."
            )
        if repeat_rate < 30:
            insight_lines.append(
                "📌 Repeat rate is below 30% — consider loyalty programs, "
                "personalized offers, or push notifications to boost retention."
            )
        elif repeat_rate > 50:
            insight_lines.append(
                "🌟 Strong repeat rate (>50%) — your customer base shows healthy loyalty. "
                "Focus on upselling and premium offerings."
            )

        if insight_lines:
            st.markdown(
                '<div class="insight-box">' + "<br>".join(insight_lines) + "</div>",
                unsafe_allow_html=True,
            )

        # ── Top loyal customers table ──────────────────────────────────────
        section_header("Top 20 Most Loyal Customers")

        @st.cache_data(ttl=120, show_spinner=False)
        def _top_loyal(start, end, city, category):
            return get_top_loyal_customers(20, start=start, end=end, city=city, food_category=category)

        loyal_data = _top_loyal(start_dt, end_dt, city, category)
        if loyal_data:
            df_loyal = pd.DataFrame(loyal_data)
            if "total_spent" in df_loyal.columns:
                df_loyal["total_spent"] = df_loyal["total_spent"].apply(fmt_currency)
            if "first_order" in df_loyal.columns:
                df_loyal["first_order"] = pd.to_datetime(df_loyal["first_order"]).dt.strftime("%Y-%m-%d")
            if "last_order" in df_loyal.columns:
                df_loyal["last_order"] = pd.to_datetime(df_loyal["last_order"]).dt.strftime("%Y-%m-%d")
            df_loyal.columns = [c.replace("_", " ").title() for c in df_loyal.columns]
            st.dataframe(df_loyal, use_container_width=True, hide_index=True, height=420)
        else:
            no_data_message("No loyal customer data.")


# ═══════════════════════════════════════════════════════════════════════════════
#  TAB 3: Discount Impact Analysis
# ═══════════════════════════════════════════════════════════════════════════════
with tab_discount:
    section_header(
        "Discount Impact Analysis",
        "How discounts affect order volume, revenue, ratings, and customer behaviour",
    )

    @st.cache_data(ttl=120, show_spinner=False)
    def _disc_overview(start, end, city, category):
        return get_discount_overview(start=start, end=end, city=city, food_category=category)

    disc = _disc_overview(start_dt, end_dt, city, category)

    if disc.get("total_orders", 0) == 0:
        no_data_message("No order data available for discount analysis.")
    else:
        # ── KPI row ────────────────────────────────────────────────────────
        cols = st.columns(4)
        kpi_card(cols[0], "Discount Usage Rate", f"{safe_round(disc.get('discount_usage_rate', 0))}%", icon="🏷️")
        kpi_card(cols[1], "Total Discount Given", fmt_currency(disc.get("total_discount_given", 0)), icon="💸")
        kpi_card(cols[2], "Avg Discount Value", fmt_currency(disc.get("avg_discount", 0)), icon="📉")
        kpi_card(cols[3], "Orders with Discount", fmt_number(disc.get("orders_with_discount", 0)), icon="🎫")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Side-by-side comparison: With vs Without Discount ──────────────
        section_header("With Discount vs Without Discount", "Head-to-head comparison")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(
                f"""
                <div class="compare-card">
                    <h4>Avg Order (With Disc.)</h4>
                    <div class="val" style="color:#34d399;">{fmt_currency(disc.get('avg_order_with_discount', 0))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"""
                <div class="compare-card">
                    <h4>Avg Order (No Disc.)</h4>
                    <div class="val">{fmt_currency(disc.get('avg_order_without_discount', 0))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c3:
            rating_w = safe_round(disc.get("avg_rating_with_discount", 0), 1)
            st.markdown(
                f"""
                <div class="compare-card">
                    <h4>Avg Rating (With Disc.)</h4>
                    <div class="val" style="color:#fbbf24;">{'⭐'} {rating_w}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c4:
            rating_wo = safe_round(disc.get("avg_rating_without_discount", 0), 1)
            st.markdown(
                f"""
                <div class="compare-card">
                    <h4>Avg Rating (No Disc.)</h4>
                    <div class="val">{'⭐'} {rating_wo}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Discount bands chart ───────────────────────────────────────────
        col_bands, col_cat = st.columns(2)

        @st.cache_data(ttl=120, show_spinner=False)
        def _disc_bands(start, end, city, category):
            return get_discount_bands(start=start, end=end, city=city, food_category=category)

        with col_bands:
            section_header("Orders by Discount Band")
            band_data = _disc_bands(start_dt, end_dt, city, category)
            if band_data:
                df_bands = pd.DataFrame(band_data)
                # Sort by a logical order
                band_order = ["No Discount", "1-5%", "5-10%", "10-15%", "15-20%", "20-30%", "30%+"]
                df_bands["sort_key"] = df_bands["band"].apply(
                    lambda b: band_order.index(b) if b in band_order else 99
                )
                df_bands = df_bands.sort_values("sort_key")

                fig_bands = px.bar(
                    df_bands,
                    x="band",
                    y="orders",
                    color="avg_rating",
                    color_continuous_scale="RdYlGn",
                    labels={"band": "Discount Band", "orders": "Orders", "avg_rating": "Avg Rating"},
                    hover_data=["avg_total", "cancellation_rate"],
                )
                fig_bands.update_layout(
                    title=dict(text="🏷️ Orders by Discount Band", font=dict(size=15, color="#e0e0e0")),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#cccccc"), height=400,
                    xaxis=dict(showgrid=False, linecolor="#333"),
                    yaxis=dict(showgrid=True, gridcolor="#333"),
                )
                st.plotly_chart(fig_bands, use_container_width=True)
            else:
                no_data_message("No discount band data.")

        # ── Discount by food category ──────────────────────────────────────
        @st.cache_data(ttl=120, show_spinner=False)
        def _disc_cat(start, end, city):
            return get_discount_by_category(start=start, end=end, city=city)

        with col_cat:
            section_header("Discount Usage by Category")
            cat_data = _disc_cat(start_dt, end_dt, city)
            if cat_data:
                df_cat = pd.DataFrame(cat_data)
                fig_cat = px.bar(
                    df_cat,
                    x="category",
                    y="discount_rate",
                    color="avg_discount",
                    color_continuous_scale="Plasma",
                    labels={"category": "Food Category", "discount_rate": "% Orders with Discount",
                            "avg_discount": "Avg Discount (₹)"},
                    hover_data=["total_orders", "avg_rating", "total_revenue"],
                )
                fig_cat.update_layout(
                    title=dict(text="🍔 Discount Rate by Category", font=dict(size=15, color="#e0e0e0")),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#cccccc"), height=400,
                    xaxis=dict(showgrid=False, linecolor="#333", tickangle=-45),
                    yaxis=dict(showgrid=True, gridcolor="#333"),
                )
                st.plotly_chart(fig_cat, use_container_width=True)
            else:
                no_data_message("No category discount data.")

        # ── Monthly discount trend ─────────────────────────────────────────
        section_header("Monthly Discount Trend")

        @st.cache_data(ttl=120, show_spinner=False)
        def _disc_trend(start, end, city, category):
            return get_discount_trend_by_month(start=start, end=end, city=city, food_category=category)

        trend_data = _disc_trend(start_dt, end_dt, city, category)
        if trend_data:
            df_trend = pd.DataFrame(trend_data)

            fig_trend = go.Figure()
            # Discount usage rate line
            fig_trend.add_trace(go.Scatter(
                x=df_trend["month"], y=df_trend["discount_rate"],
                name="Discount Usage %",
                line=dict(color="#f472b6", width=2.5),
                mode="lines+markers",
                marker=dict(size=6),
                yaxis="y",
            ))
            # Avg discount bar
            fig_trend.add_trace(go.Bar(
                x=df_trend["month"], y=df_trend["avg_discount"],
                name="Avg Discount (₹)",
                marker_color="rgba(108,99,255,0.4)",
                yaxis="y2",
            ))

            fig_trend.update_layout(
                title=dict(text="📈 Discount Trend Over Time", font=dict(size=16, color="#e0e0e0")),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#cccccc"), height=400,
                legend=dict(bgcolor="rgba(0,0,0,0.3)", bordercolor="#444", x=0, y=1.15, orientation="h"),
                xaxis=dict(showgrid=False, linecolor="#333"),
                yaxis=dict(
                    title="Discount Usage %", showgrid=True, gridcolor="#333",
                    side="left", linecolor="#333",
                ),
                yaxis2=dict(
                    title="Avg Discount (₹)", overlaying="y", side="right",
                    showgrid=False, linecolor="#333",
                ),
                hoverlabel=dict(bgcolor="#1e2130", font_color="#ffffff"),
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            no_data_message("No monthly trend data available.")

        # ── Discount insight box ───────────────────────────────────────────
        disc_insights = []
        usage = disc.get("discount_usage_rate", 0)
        avg_w = disc.get("avg_order_with_discount", 0)
        avg_wo = disc.get("avg_order_without_discount", 0)
        r_w = disc.get("avg_rating_with_discount", 0) or 0
        r_wo = disc.get("avg_rating_without_discount", 0) or 0

        disc_insights.append(
            f"🏷️ <strong>{safe_round(usage)}%</strong> of orders used a discount, "
            f"with a total of <strong>{fmt_currency(disc.get('total_discount_given', 0))}</strong> given."
        )

        if avg_w and avg_wo:
            if avg_w > avg_wo:
                pct_diff = round((avg_w - avg_wo) / max(avg_wo, 1) * 100, 1)
                disc_insights.append(
                    f"📈 Discounted orders have <strong>{pct_diff}% higher</strong> average order value "
                    f"({fmt_currency(avg_w)} vs {fmt_currency(avg_wo)}) — "
                    f"discounts may encourage larger orders."
                )
            else:
                pct_diff = round((avg_wo - avg_w) / max(avg_wo, 1) * 100, 1)
                disc_insights.append(
                    f"📉 Non-discounted orders have <strong>{pct_diff}% higher</strong> average order value "
                    f"({fmt_currency(avg_wo)} vs {fmt_currency(avg_w)})."
                )

        if r_w and r_wo:
            diff = round(r_w - r_wo, 1)
            if abs(diff) > 0.1:
                direction = "higher" if diff > 0 else "lower"
                disc_insights.append(
                    f"⭐ Discounted orders receive <strong>{abs(diff)} points {direction}</strong> "
                    f"average rating ({r_w} vs {r_wo})."
                )

        if disc_insights:
            st.markdown(
                '<div class="insight-box">' + "<br>".join(disc_insights) + "</div>",
                unsafe_allow_html=True,
            )
