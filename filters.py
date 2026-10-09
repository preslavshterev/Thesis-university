import pandas as pd
import streamlit as st

from data_access import load_completed_sales, load_stores

FILTER_KEYS = ("period", "stores", "categories")


def reset_filters():
    for key in FILTER_KEYS:
        st.session_state.pop(key, None)


def render_sidebar_filters():
    try:
        sales = load_completed_sales()
        stores = load_stores()
    except FileNotFoundError:
        return

    first = sales["order_date"].min().date()
    last = sales["order_date"].max().date()
    store_names = sorted(stores["store_name"])
    categories = sorted(sales["category_name"].dropna().unique())

    st.sidebar.header("Filters")
    st.sidebar.date_input("Period", value=(first, last), min_value=first, max_value=last, key="period")
    st.sidebar.multiselect("Stores", options=store_names, default=store_names, key="stores")
    st.sidebar.multiselect("Categories", options=categories, default=categories, key="categories")
    st.sidebar.button("Reset filters", on_click=reset_filters)
    st.sidebar.caption("Filters apply to Dashboard, Sales and Products.")


def filter_sales(df, stores, period, store_names, categories):
    start = pd.Timestamp(period[0])
    end = pd.Timestamp(period[1] if len(period) == 2 else period[0])

    store_ids = stores.loc[stores["store_name"].isin(store_names), "store_id"]

    mask = (
        (df["order_date"] >= start)
        & (df["order_date"] < end + pd.Timedelta(days=1))
        & df["store_id"].isin(store_ids)
        & df["category_name"].isin(categories)
    )
    return df[mask]


def apply_filters(df):
    return filter_sales(
        df,
        load_stores(),
        st.session_state["period"],
        st.session_state["stores"],
        st.session_state["categories"],
    )


def get_filtered_sales():
    return apply_filters(load_completed_sales())


def describe_filters():
    period = st.session_state["period"]
    period_text = f"{period[0]} to {period[1]}" if len(period) == 2 else str(period[0])
    return pd.DataFrame({
        "filter": ["Period", "Stores", "Categories"],
        "value": [
            period_text,
            ", ".join(st.session_state["stores"]),
            ", ".join(st.session_state["categories"]),
        ],
    })