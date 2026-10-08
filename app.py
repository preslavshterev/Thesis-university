import streamlit as st

from filters import render_sidebar_filters

st.set_page_config(page_title="Sales Analytics", layout="wide")

render_sidebar_filters()

pages = [
    st.Page("views/home.py", title="Dashboard", default=True),
    st.Page("views/sales_page.py", title="Sales"),
    st.Page("views/customers_page.py", title="Customers"),
    st.Page("views/products_page.py", title="Products"),
    st.Page("views/inventory_page.py", title="Inventory"),
    st.Page("views/forecast_page.py", title="Forecast"),
]

navigation = st.navigation(pages)
navigation.run()