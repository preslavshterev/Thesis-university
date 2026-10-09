import plotly.express as px
import streamlit as st

from data_access import load_inventory_table
from formatting import format_money
from inventory import low_stock_items, stock_by_store, stock_value_by_category
from ui import PRIMARY, card, chart_card, metric_card, page_header, style_chart

page_header("Inventory", "Current stock by store and category (a snapshot, sidebar filters do not apply).")

try:
    table = load_inventory_table()
except FileNotFoundError as error:
    st.error(
        f"A required data file is missing ({error}). "
        "Run export_tables.py first."
    )
    st.stop()

with card("Threshold"):
    threshold = st.slider("Low stock threshold (units)", min_value=0, max_value=100, value=20)

columns = st.columns(4)
metric_card(columns[0], "Units in stock", f"{table['quantity_available'].sum():,}")
metric_card(columns[1], "Stock value (at cost)", format_money(table["stock_value"].sum()))
metric_card(columns[2], "Out of stock", f"{(table['quantity_available'] == 0).sum():,}")
metric_card(
    columns[3],
    "Low stock",
    f"{(table['quantity_available'] <= threshold).sum():,}",
    help="Product-store pairs at or below the threshold",
)

fig_store = px.bar(
    stock_by_store(table), x="store_name", y="units",
    labels={"store_name": "Store", "units": "Units"},
    color_discrete_sequence=[PRIMARY],
)
fig_category = px.bar(
    stock_value_by_category(table), x="stock_value", y="category_name", orientation="h",
    labels={"stock_value": "Stock value", "category_name": "Category"},
    color_discrete_sequence=[PRIMARY],
)
fig_category.update_layout(yaxis={"categoryorder": "total ascending"})

left, right = st.columns(2)
with left:
    chart_card("Units by store", style_chart(fig_store))
with right:
    chart_card("Stock value by category", style_chart(fig_category, money_axis="x"))

with card("Low stock items"):
    st.subheader("Low stock items")
    st.dataframe(low_stock_items(table, threshold), hide_index=True)