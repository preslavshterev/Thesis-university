import plotly.express as px
import streamlit as st

from data_access import load_inventory_table
from formatting import CURRENCY_SYMBOL, format_money
from inventory import low_stock_items, stock_by_store, stock_value_by_category

BAR_COLOR = "#2E6F9E"

st.title("Inventory")

try:
    table = load_inventory_table()
except FileNotFoundError as error:
    st.error(
        f"A required data file is missing ({error}). "
        "Run export_tables.py first."
    )
    st.stop()

threshold = st.slider("Low stock threshold (units)", min_value=0, max_value=100, value=20)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Units in stock", f"{table['quantity_available'].sum():,}")
col2.metric("Stock value (at cost)", format_money(table["stock_value"].sum()))
col3.metric("Out of stock", f"{(table['quantity_available'] == 0).sum():,}")
col4.metric(
    "Low stock",
    f"{(table['quantity_available'] <= threshold).sum():,}",
    help="Product-store pairs at or below the threshold",
)

left, right = st.columns(2)

with left:
    st.subheader("Units by store")
    fig_store = px.bar(
        stock_by_store(table),
        x="store_name",
        y="units",
        labels={"store_name": "Store", "units": "Units"},
        color_discrete_sequence=[BAR_COLOR],
    )
    st.plotly_chart(fig_store)

with right:
    st.subheader("Stock value by category")
    fig_category = px.bar(
        stock_value_by_category(table),
        x="stock_value",
        y="category_name",
        orientation="h",
        labels={"stock_value": "Stock value", "category_name": "Category"},
        color_discrete_sequence=[BAR_COLOR],
    )
    fig_category.update_layout(
        xaxis_tickprefix=CURRENCY_SYMBOL,
        xaxis_tickformat=",",
        yaxis={"categoryorder": "total ascending"},
    )
    st.plotly_chart(fig_category)

st.subheader("Low stock items")
st.dataframe(low_stock_items(table, threshold), hide_index=True)