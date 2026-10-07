import streamlit as st

from data_access import load_fact_sales, load_rfm

st.title("Sales Analytics Dashboard")

try:
    fact_sales = load_fact_sales()
    rfm = load_rfm()
except FileNotFoundError as error:
    st.error(
        f"A required data file is missing ({error}). "
        "Run etl_pipeline.py and customers.py first."
    )
    st.stop()

st.subheader("Data connection check")

col1, col2, col3 = st.columns(3)
col1.metric("Sales lines", f"{len(fact_sales):,}")
col2.metric("Customers with RFM data", f"{len(rfm):,}")
col3.metric("Latest order date", fact_sales["order_date"].max().strftime("%Y-%m-%d"))

st.dataframe(fact_sales.head(10))