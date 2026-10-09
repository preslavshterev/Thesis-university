import streamlit as st

from auth import render_logout, require_login
from filters import render_sidebar_filters
from ui import apply_styles

st.set_page_config(
    page_title="Sales Analytics",
    page_icon=":material/bar_chart:",
    layout="wide",
)

apply_styles()
require_login()
render_sidebar_filters()
render_logout()

pages = [
    st.Page("views/home.py", title="Dashboard", icon=":material/dashboard:", default=True),
    st.Page("views/sales_page.py", title="Sales", icon=":material/trending_up:"),
    st.Page("views/customers_page.py", title="Customers", icon=":material/group:"),
    st.Page("views/products_page.py", title="Products", icon=":material/inventory_2:"),
    st.Page("views/inventory_page.py", title="Inventory", icon=":material/warehouse:"),
    st.Page("views/forecast_page.py", title="Forecast", icon=":material/query_stats:"),
    st.Page("views/reports_page.py", title="Reports", icon=":material/download:"),
]

navigation = st.navigation(pages)
navigation.run()