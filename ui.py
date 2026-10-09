import re
from pathlib import Path

import plotly.express as px
import streamlit as st

from formatting import CURRENCY_SYMBOL

PRIMARY = "#4DA3FF"
ACCENT = "#FFB547"
POSITIVE = "#3DDC97"
CATEGORY_COLORS = [PRIMARY, ACCENT, POSITIVE, "#B58CFF", "#FF6B6B", "#9AA7B8"]
HEATMAP_SCALE = ["#1B2A44", PRIMARY]
FORECAST_BAND = "rgba(255, 181, 71, 0.2)"
GRID = "rgba(160, 175, 200, 0.15)"
STYLE_PATH = Path(__file__).resolve().parent / "style.css"

HOVER_Y = f"{CURRENCY_SYMBOL}%{{y:,.2f}}"
HOVER_X = f"{CURRENCY_SYMBOL}%{{x:,.2f}}"


def apply_styles():
    css = STYLE_PATH.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def card(name, kind="card"):
    key = f"{kind}_{re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')}"
    try:
        return st.container(key=key)
    except TypeError:
        return st.container(border=True)


def page_header(title, description):
    st.title(title)
    st.caption(description)


def stop_if_empty(df):
    if df.empty:
        st.warning("No sales match the selected filters.")
        st.stop()


def metric_card(column, label, value, help=None):
    with column:
        with card(label, kind="metric"):
            st.metric(label, value, help=help)


def chart_card(title, fig):
    with card(title):
        st.subheader(title)
        st.plotly_chart(fig)


def style_chart(fig, money_axis=None, height=360):
    fig.update_layout(
        height=height,
        margin={"l": 10, "r": 10, "t": 30, "b": 10},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
    )
    fig.update_xaxes(gridcolor=GRID)
    fig.update_yaxes(gridcolor=GRID)
    if money_axis:
        fig.update_layout(**{
            f"{money_axis}axis_tickprefix": CURRENCY_SYMBOL,
            f"{money_axis}axis_tickformat": ",",
        })
    return fig


def monthly_revenue_figure(monthly):
    fig = px.line(
        monthly, x="period", y="line_total", markers=True,
        labels={"period": "Month", "line_total": "Revenue"},
        color_discrete_sequence=[PRIMARY],
    )
    fig.update_traces(hovertemplate=HOVER_Y, line={"width": 3}, marker={"size": 7})
    return style_chart(fig, money_axis="y")


def category_revenue_figure(by_category):
    fig = px.bar(
        by_category, x="line_total", y="category_name", orientation="h",
        labels={"line_total": "Revenue", "category_name": "Category"},
        color_discrete_sequence=[PRIMARY],
    )
    fig.update_traces(hovertemplate=HOVER_X)
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    return style_chart(fig, money_axis="x")


def store_revenue_figure(by_store):
    fig = px.bar(
        by_store, x="store_name", y="line_total",
        labels={"store_name": "Store", "line_total": "Revenue"},
        color_discrete_sequence=[PRIMARY],
    )
    fig.update_traces(hovertemplate=HOVER_Y)
    return style_chart(fig, money_axis="y")