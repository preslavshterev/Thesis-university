import streamlit as st

st.set_page_config(page_title="Sales Analytics", layout="wide")

pages = [
    st.Page("views/home.py", title="Dashboard", default=True),
    st.Page("views/sales_page.py", title="Sales"),
]

navigation = st.navigation(pages)
navigation.run()