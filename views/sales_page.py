import plotly.express as px
import streamlit as st

from data_access import load_completed_sales, load_stores
from formatting import CURRENCY_SYMBOL
from sales import revenue_by_category, revenue_by_month, revenue_by_store

BAR_COLOR = "#2E6F9E"
MONEY_HOVER = f"{CURRENCY_SYMBOL}%{{y:,.2f}}"
MONEY_HOVER_H = f"{CURRENCY_SYMBOL}%{{x:,.2f}}"

st.title("Sales")

try:
    completed = load_completed_sales()
    stores = load_stores()
except FileNotFoundError as error:
    st.error(
        f"A required data file is missing ({error}). "
        "Run etl_pipeline.py and export_tables.py first."
    )
    st.stop()

monthly = revenue_by_month(completed)
by_category = revenue_by_category(completed)
by_store = revenue_by_store(completed, stores)

st.subheader("Monthly revenue")
fig_month = px.line(
    monthly,
    x="period",
    y="line_total",
    markers=True,
    labels={"period": "Month", "line_total": "Revenue"},
    color_discrete_sequence=[BAR_COLOR],
)
fig_month.update_traces(hovertemplate=MONEY_HOVER)
fig_month.update_layout(yaxis_tickprefix=CURRENCY_SYMBOL, yaxis_tickformat=",")
st.plotly_chart(fig_month)

left, right = st.columns(2)

with left:
    st.subheader("Revenue by category")
    fig_category = px.bar(
        by_category,
        x="line_total",
        y="category_name",
        orientation="h",
        labels={"line_total": "Revenue", "category_name": "Category"},
        color_discrete_sequence=[BAR_COLOR],
    )
    fig_category.update_traces(hovertemplate=MONEY_HOVER_H)
    fig_category.update_layout(
        xaxis_tickprefix=CURRENCY_SYMBOL,
        xaxis_tickformat=",",
        yaxis={"categoryorder": "total ascending"},
    )
    st.plotly_chart(fig_category)

with right:
    st.subheader("Revenue by store")
    fig_store = px.bar(
        by_store,
        x="store_name",
        y="line_total",
        labels={"store_name": "Store", "line_total": "Revenue"},
        color_discrete_sequence=[BAR_COLOR],
    )
    fig_store.update_traces(hovertemplate=MONEY_HOVER)
    fig_store.update_layout(yaxis_tickprefix=CURRENCY_SYMBOL, yaxis_tickformat=",")
    st.plotly_chart(fig_store)