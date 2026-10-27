"""
utils/helpers.py
Miscellaneous helper functions for the Streamlit dashboard.
"""
from __future__ import annotations
import streamlit as st
from datetime import datetime, timedelta, date


def sidebar_date_filter(key_prefix: str = "global") -> tuple[datetime | None, datetime | None]:
    """Render start/end date pickers in the sidebar. Returns (start_dt, end_dt)."""
    st.sidebar.subheader("📅 Date Range")
    today = date.today()
    # Default to 2023-01-01 to ensure the sample dataset (2023–2024) is always visible
    default_start = date(2023, 1, 1)

    col1, col2 = st.sidebar.columns(2)
    with col1:
        start = st.date_input("From", value=default_start, key=f"{key_prefix}_start")
    with col2:
        end = st.date_input("To", value=today, key=f"{key_prefix}_end")

    if start and end and start > end:
        st.sidebar.error("Start date must be before end date.")
        return None, None

    start_dt = datetime(start.year, start.month, start.day) if start else None
    end_dt = datetime(end.year, end.month, end.day, 23, 59, 59) if end else None
    return start_dt, end_dt


def sidebar_filter_select(options: list, label: str, key: str) -> str | None:
    """Render a select box; return None when 'All' is selected."""
    val = st.sidebar.selectbox(label, options, key=key)
    return None if val == "All" else val


def kpi_card(col, label: str, value: str, delta: str = "", icon: str = "") -> None:
    """Render a styled KPI card inside a Streamlit column."""
    with col:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #1e2130 0%, #252d3d 100%);
                border-radius: 12px;
                padding: 20px 24px;
                border: 1px solid #2e3850;
                text-align: center;
                min-height: 110px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            ">
                <div style="font-size:28px; margin-bottom:4px;">{icon}</div>
                <div style="font-size:26px; font-weight:700; color:#ffffff; letter-spacing:-0.5px;">{value}</div>
                <div style="font-size:12px; color:#8892a4; margin-top:6px; text-transform:uppercase; letter-spacing:1px;">{label}</div>
                {"<div style='font-size:12px; color:#4ade80; margin-top:4px;'>" + delta + "</div>" if delta else ""}
            </div>
            """,
            unsafe_allow_html=True,
        )


def section_header(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div style="margin: 24px 0 16px 0;">
            <h2 style="color:#e0e0e0; margin:0; font-size:22px; font-weight:700;">{title}</h2>
            {"<p style='color:#8892a4; margin:4px 0 0 0; font-size:14px;'>" + subtitle + "</p>" if subtitle else ""}
        </div>
        <hr style="border:none; border-top:1px solid #2e3850; margin:0 0 16px 0;">
        """,
        unsafe_allow_html=True,
    )


def no_data_message(message: str = "No data found for the selected filters.") -> None:
    st.info(f"ℹ️ {message}", icon=None)


def safe_round(value, decimals: int = 2) -> float:
    try:
        return round(float(value or 0), decimals)
    except (TypeError, ValueError):
        return 0.0
