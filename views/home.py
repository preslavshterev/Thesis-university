import streamlit as st

from data_access import load_rfm
from filters import get_filtered_sales
from formatting import format_money
from sales import generate_kpi_summary

st.title("Sales Analytics Dashboard")

try:
    filtered = get_filtered_sales()
    rfm = load_rfm()
except FileNotFoundError as error:
    st.error(
        f"A required data file is missing ({error}). "
        "Run etl_pipeline.py, customers.py and export_tables.py first."
    )
    st.stop()

if filtered.empty:
    st.warning("No sales match the selected filters.")
    st.stop()

kpis = generate_kpi_summary(filtered)
profit_margin = kpis["total_profit"] / kpis["total_revenue"] * 100

st.subheader("Key performance indicators")
st.caption("Completed orders, filtered by the sidebar selection")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total revenue", format_money(kpis["total_revenue"]))
col2.metric(
    "Total profit",
    format_money(kpis["total_profit"]),
    help=f"Profit margin: {profit_margin:.1f}% of revenue",
)
col3.metric("Orders", f"{kpis['order_count']:,}")
col4.metric("Average order value", format_money(kpis["average_order_value"]))

with st.expander("Data overview"):
    st.write(
        f"{len(filtered):,} sales lines match the filters. "
        f"{len(rfm):,} customers with RFM data (not filtered)."
    )
    st.dataframe(filtered.head(10))