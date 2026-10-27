"""
utils/charts.py
Reusable Plotly chart factory functions.
All functions accept a list-of-dicts (from MongoDB) and return a Plotly figure.
"""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Any

# Colour palette
_PRIMARY = "#6C63FF"
_PALETTE = px.colors.qualitative.Vivid
_SEQUENTIAL = px.colors.sequential.Plasma

_EMPTY_STYLE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#cccccc"),
)


def _empty_fig(message: str = "No data available") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=16, color="#888"),
    )
    fig.update_layout(**_EMPTY_STYLE, height=300)
    return fig


def _base_layout(fig: go.Figure, title: str, height: int = 400) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color="#e0e0e0")),
        paper_bgcolor="rgba(14,17,23,0.0)",
        plot_bgcolor="rgba(14,17,23,0.0)",
        font=dict(color="#cccccc", family="Inter, Roboto, sans-serif"),
        legend=dict(bgcolor="rgba(0,0,0,0.3)", bordercolor="#444"),
        height=height,
        margin=dict(l=20, r=20, t=50, b=20),
        hoverlabel=dict(bgcolor="#1e2130", font_color="#ffffff"),
    )
    fig.update_xaxes(showgrid=False, linecolor="#333")
    fig.update_yaxes(showgrid=True, gridcolor="#333", linecolor="#333")
    return fig


# ── Line charts ───────────────────────────────────────────────────────────────

def line_revenue_trend(data: list[dict], x_field: str, title: str) -> go.Figure:
    if not data:
        return _empty_fig("No revenue data for the selected period.")
    df = pd.DataFrame(data)
    fig = px.line(
        df,
        x=x_field,
        y="revenue",
        markers=True,
        color_discrete_sequence=[_PRIMARY],
    )
    fig.update_traces(line=dict(width=2.5), marker=dict(size=5))
    return _base_layout(fig, title)


def line_order_trend(data: list[dict], x_field: str, title: str) -> go.Figure:
    if not data:
        return _empty_fig("No order data for the selected period.")
    df = pd.DataFrame(data)
    fig = px.line(
        df,
        x=x_field,
        y="orders",
        markers=True,
        color_discrete_sequence=["#FF6B6B"],
    )
    fig.update_traces(line=dict(width=2.5), marker=dict(size=5))
    return _base_layout(fig, title)


# ── Bar charts ────────────────────────────────────────────────────────────────

def bar_horizontal(
    data: list[dict],
    x: str,
    y: str,
    title: str,
    color: str = _PRIMARY,
    height: int = 400,
) -> go.Figure:
    if not data:
        return _empty_fig()
    df = pd.DataFrame(data).sort_values(x, ascending=True)
    fig = px.bar(df, x=x, y=y, orientation="h", color_discrete_sequence=[color])
    fig.update_traces(marker_line_width=0)
    return _base_layout(fig, title, height=height)


def bar_vertical(
    data: list[dict],
    x: str,
    y: str,
    title: str,
    color: str = _PRIMARY,
    height: int = 400,
) -> go.Figure:
    if not data:
        return _empty_fig()
    df = pd.DataFrame(data)
    fig = px.bar(df, x=x, y=y, color_discrete_sequence=[color])
    fig.update_traces(marker_line_width=0)
    return _base_layout(fig, title, height=height)


def bar_grouped(
    data: list[dict],
    x: str,
    y_cols: list[str],
    title: str,
    height: int = 400,
) -> go.Figure:
    if not data:
        return _empty_fig()
    df = pd.DataFrame(data)
    fig = px.bar(df, x=x, y=y_cols, barmode="group", color_discrete_sequence=_PALETTE)
    return _base_layout(fig, title, height=height)


# ── Pie / Donut charts ────────────────────────────────────────────────────────

def donut_chart(
    data: list[dict],
    names: str,
    values: str,
    title: str,
    height: int = 380,
) -> go.Figure:
    if not data:
        return _empty_fig()
    df = pd.DataFrame(data)
    fig = px.pie(
        df,
        names=names,
        values=values,
        hole=0.45,
        color_discrete_sequence=_PALETTE,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Count: %{value:,}<br>Share: %{percent}",
    )
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color="#e0e0e0")),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#cccccc"),
        height=height,
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(bgcolor="rgba(0,0,0,0.3)"),
    )
    return fig


# ── Histogram ─────────────────────────────────────────────────────────────────

def histogram(
    data: list[dict],
    x: str,
    title: str,
    nbins: int = 20,
    height: int = 380,
) -> go.Figure:
    if not data:
        return _empty_fig()
    df = pd.DataFrame(data)
    if x not in df.columns or df[x].dropna().empty:
        return _empty_fig(f"No '{x}' data available.")
    fig = px.histogram(
        df,
        x=x,
        nbins=nbins,
        color_discrete_sequence=[_PRIMARY],
    )
    return _base_layout(fig, title, height=height)


# ── Scatter plot ──────────────────────────────────────────────────────────────

def scatter_plot(
    data: list[dict],
    x: str,
    y: str,
    color: str | None = None,
    title: str = "",
    height: int = 400,
) -> go.Figure:
    if not data:
        return _empty_fig()
    df = pd.DataFrame(data)
    kwargs: dict[str, Any] = dict(
        x=x, y=y, color_discrete_sequence=_PALETTE, opacity=0.7
    )
    if color and color in df.columns:
        kwargs["color"] = color
    fig = px.scatter(df, **kwargs)
    return _base_layout(fig, title, height=height)


# ── Heatmap ───────────────────────────────────────────────────────────────────

def heatmap_day_hour(data: list[dict], title: str = "Order Activity Heatmap") -> go.Figure:
    if not data:
        return _empty_fig("No heatmap data available.")

    day_names = {1: "Sun", 2: "Mon", 3: "Tue", 4: "Wed", 5: "Thu", 6: "Fri", 7: "Sat"}
    df = pd.DataFrame(data)

    # Build full 7×24 grid
    pivot = pd.DataFrame(0, index=list(day_names.values()), columns=list(range(24)))
    for _, row in df.iterrows():
        day_label = day_names.get(int(row["day"]), "?")
        hour = int(row["hour"])
        if day_label in pivot.index and hour in pivot.columns:
            pivot.loc[day_label, hour] = int(row["orders"])

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values.tolist(),
            x=[f"{h:02d}:00" for h in range(24)],
            y=list(day_names.values()),
            colorscale="Plasma",
            hoverongaps=False,
            hovertemplate="Day: %{y}<br>Hour: %{x}<br>Orders: %{z}<extra></extra>",
        )
    )
    return _base_layout(fig, title, height=350)


# ── KPI card helper (returns formatted string) ────────────────────────────────

def fmt_currency(value: float) -> str:
    if value >= 1_000_000:
        return f"₹{value/1_000_000:.2f}M"
    if value >= 1_000:
        return f"₹{value/1_000:.1f}K"
    return f"₹{value:,.0f}"


def fmt_number(value: float | int) -> str:
    if value >= 1_000_000:
        return f"{value/1_000_000:.2f}M"
    if value >= 1_000:
        return f"{value/1_000:.1f}K"
    return f"{value:,}"
