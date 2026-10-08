import streamlit as st

st.set_page_config(page_title="Sales Analytics", layout="wide")

pages = [
    st.Page("views/home.py", title="Dashboard", default=True),
    st.Page("views/sales_page.py", title="Sales"),
    st.Page("views/customers_page.py", title="Customers"),
    st.Page("views/products_page.py", title="Products"),
]

navigation = st.navigation(pages)
navigation.run()