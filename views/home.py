import streamlit as st

from filters import get_filtered_sales
from formatting import format_money
from sales import generate_kpi_summary, revenue_by_category, revenue_by_month
from ui import (
    category_revenue_figure,
    chart_card,
    metric_card,
    monthly_revenue_figure,
    page_header,
    stop_if_empty,
)

page_header("Sales Analytics Dashboard", "Overview of completed orders for the selected filters.")

try:
    filtered = get_filtered_sales()
except FileNotFoundError as error:
    st.error(
        f"A required data file is missing ({error}). "
        "Run etl_pipeline.py and export_tables.py first."
    )
    st.stop()

stop_if_empty(filtered)

kpis = generate_kpi_summary(filtered)
profit_margin = kpis["total_profit"] / kpis["total_revenue"] * 100

columns = st.columns(4)
metric_card(columns[0], "Total revenue", format_money(kpis["total_revenue"]))
metric_card(
    columns[1],
    "Total profit",
    format_money(kpis["total_profit"]),
    help=f"Profit margin: {profit_margin:.1f}% of revenue",
)
metric_card(columns[2], "Orders", f"{kpis['order_count']:,}")
metric_card(columns[3], "Average order value", format_money(kpis["average_order_value"]))

left, right = st.columns([3, 2])
with left:
    chart_card("Monthly revenue", monthly_revenue_figure(revenue_by_month(filtered)))
with right:
    chart_card("Revenue by category", category_revenue_figure(revenue_by_category(filtered)))

first = filtered["order_date"].min()
last = filtered["order_date"].max()
st.caption(f"Data shown: {first:%Y-%m-%d} to {last:%Y-%m-%d}, {len(filtered):,} sales lines.")