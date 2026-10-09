import streamlit as st

from data_access import load_stores
from filters import get_filtered_sales
from sales import revenue_by_category, revenue_by_month, revenue_by_store
from ui import (
    category_revenue_figure,
    chart_card,
    monthly_revenue_figure,
    page_header,
    stop_if_empty,
    store_revenue_figure,
)

page_header("Sales", "Revenue over time, by category and by store.")

try:
    completed = get_filtered_sales()
    stores = load_stores()
except FileNotFoundError as error:
    st.error(
        f"A required data file is missing ({error}). "
        "Run etl_pipeline.py and export_tables.py first."
    )
    st.stop()

stop_if_empty(completed)

chart_card("Monthly revenue", monthly_revenue_figure(revenue_by_month(completed)))

left, right = st.columns(2)
with left:
    chart_card("Revenue by category", category_revenue_figure(revenue_by_category(completed)))
with right:
    chart_card("Revenue by store", store_revenue_figure(revenue_by_store(completed, stores)))