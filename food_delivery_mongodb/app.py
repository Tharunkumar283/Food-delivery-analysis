"""
app.py
Main Streamlit entry-point for the Online Food Delivery Analysis dashboard.
Run with:  streamlit run app.py
"""
import sys
import os

# Ensure project root is on sys.path so sub-packages are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from database.connection import ping
from config.settings import settings

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title=settings.APP_TITLE,
    page_icon="🍕",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": f"**{settings.APP_TITLE}** | MongoDB Big Data Analytics Project",
    },
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Dark background */
    .stApp {
        background: linear-gradient(160deg, #0d1117 0%, #111827 100%);
        color: #e0e0e0;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111827 0%, #0d1117 100%);
        border-right: 1px solid #1f2a3c;
    }
    section[data-testid="stSidebar"] * {
        color: #c9d1d9 !important;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e2130, #252d3d);
        border: 1px solid #2e3850;
        border-radius: 12px;
        padding: 16px;
    }
    div[data-testid="stMetric"] label {
        color: #8892a4 !important;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-size: 26px !important;
        font-weight: 700 !important;
        color: #ffffff !important;
    }

    /* Headers */
    h1, h2, h3 { color: #e0e0e0 !important; font-weight: 700 !important; }

    /* DataFrames */
    .stDataFrame { border-radius: 8px; overflow: hidden; }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #6C63FF, #4f46e5);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 10px 24px;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(108, 99, 255, 0.4);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #1a1f2e;
        border-radius: 10px;
        padding: 4px;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #8892a4;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6C63FF, #4f46e5);
        color: white !important;
    }

    /* Selectboxes */
    .stSelectbox label, .stMultiSelect label { color: #8892a4 !important; }

    /* Progress bar */
    .stProgress > div > div { background: linear-gradient(90deg, #6C63FF, #a78bfa); }

    /* Divider */
    hr { border-color: #2e3850 !important; }

    /* Cards / containers */
    .chart-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #1e2436 100%);
        border: 1px solid #2e3850;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
    }

    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar branding ──────────────────────────────────────────────────────────
st.sidebar.markdown(
    """
    <div style="text-align:center; padding: 20px 0 10px 0;">
        <div style="font-size:40px;">🍕</div>
        <h2 style="color:#6C63FF; margin:8px 0 4px 0; font-size:16px; font-weight:700;">
            Food Delivery Analytics
        </h2>
        <p style="color:#555; font-size:11px; margin:0;">MongoDB · Streamlit · Plotly</p>
    </div>
    <hr style="border-color:#2e3850; margin:10px 0;">
    """,
    unsafe_allow_html=True,
)

# ── DB connection banner ──────────────────────────────────────────────────────
db_ok = ping()
if db_ok:
    st.sidebar.success("✅ MongoDB Connected", icon=None)
else:
    st.sidebar.error("❌ MongoDB Offline – start your server and refresh.")

# ── Home page ─────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="
        background: linear-gradient(135deg, #1a1f2e 0%, #252d3d 100%);
        border-radius: 16px;
        padding: 48px;
        border: 1px solid #2e3850;
        text-align: center;
        margin-bottom: 32px;
    ">
        <div style="font-size: 64px; margin-bottom: 16px;">🍕</div>
        <h1 style="
            font-size: 36px;
            font-weight: 800;
            background: linear-gradient(135deg, #6C63FF, #a78bfa, #ec4899);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0 0 12px 0;
        ">Online Food Delivery Analysis</h1>
        <p style="color: #8892a4; font-size: 18px; max-width: 600px; margin: 0 auto 24px auto;">
            Using MongoDB for Big Data Processing
        </p>
        <div style="display: flex; justify-content: center; gap: 12px; flex-wrap: wrap;">
            <span style="background:#1f2d4a; color:#60a5fa; padding:6px 16px; border-radius:20px; font-size:13px;">🗄️ MongoDB</span>
            <span style="background:#1f2d4a; color:#34d399; padding:6px 16px; border-radius:20px; font-size:13px;">🐍 Python</span>
            <span style="background:#1f2d4a; color:#f472b6; padding:6px 16px; border-radius:20px; font-size:13px;">📊 Streamlit</span>
            <span style="background:#1f2d4a; color:#a78bfa; padding:6px 16px; border-radius:20px; font-size:13px;">📈 Plotly</span>
            <span style="background:#1f2d4a; color:#fbbf24; padding:6px 16px; border-radius:20px; font-size:13px;">🐼 Pandas</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Project info grid ─────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(
        """
        <div style="background:#1a1f2e; border:1px solid #2e3850; border-radius:12px; padding:24px;">
            <h3 style="color:#6C63FF; margin:0 0 12px 0;">🎯 Objective</h3>
            <p style="color:#8892a4; font-size:14px; line-height:1.6; margin:0;">
            Analyze large-scale food delivery data to uncover customer behavior patterns,
            restaurant performance metrics, delivery efficiency, and revenue trends using
            MongoDB aggregation pipelines.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        """
        <div style="background:#1a1f2e; border:1px solid #2e3850; border-radius:12px; padding:24px;">
            <h3 style="color:#34d399; margin:0 0 12px 0;">📦 Modules</h3>
            <ul style="color:#8892a4; font-size:14px; margin:0; padding-left:18px; line-height:2;">
                <li>📊 Overview Dashboard</li>
                <li>💰 Sales & Revenue Analysis</li>
                <li>👥 Customer & Order Patterns</li>
                <li>🏪 Restaurant Performance</li>
                <li>🚚 Delivery Analytics</li>
                <li>🔍 Data Explorer & Export</li>
                <li>🧠 Advanced Analytics (RFM, Loyalty, Discount)</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        """
        <div style="background:#1a1f2e; border:1px solid #2e3850; border-radius:12px; padding:24px;">
            <h3 style="color:#f472b6; margin:0 0 12px 0;">⚡ Features</h3>
            <ul style="color:#8892a4; font-size:14px; margin:0; padding-left:18px; line-height:2;">
                <li>Batch CSV import with validation</li>
                <li>MongoDB aggregation pipelines</li>
                <li>Interactive Plotly visualizations</li>
                <li>Global date + category filters</li>
                <li>Paginated data explorer</li>
                <li>CSV export for filtered data</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)
st.info(
    "👈 **Use the sidebar** to navigate between analytics pages. "
    "Make sure MongoDB is running and data has been imported before viewing dashboards.",
    icon=None,
)

# ── Quick-start instructions ──────────────────────────────────────────────────
with st.expander("🚀 Quick Start Guide", expanded=not db_ok):
    st.markdown(
        """
        ### Getting Started

        **1. Install dependencies**
        ```bash
        pip install -r requirements.txt
        ```

        **2. Set up environment**
        ```bash
        copy .env.example .env
        # Edit .env with your MongoDB URI
        ```

        **3. Start MongoDB** (if local)
        ```bash
        mongod --dbpath C:/data/db
        ```

        **4. Import sample data**
        ```bash
        python -m ingestion.import_data data/food_delivery_sample.csv
        ```

        **5. Create indexes**
        ```bash
        python -m database.indexes
        ```

        **6. Open the dashboard pages** from the sidebar ←
        """
    )
