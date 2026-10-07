import streamlit as st

st.set_page_config(page_title="Sales Analytics", layout="wide")

pages = [
    st.Page("views/home.py", title="Dashboard", default=True),
]

navigation = st.navigation(pages)
navigation.run()