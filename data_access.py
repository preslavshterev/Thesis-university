from pathlib import Path

import pandas as pd
import streamlit as st

from products import flag_promotion_orders

OUTPUT_DIR = Path(__file__).resolve().parent / "output"


@st.cache_data
def load_fact_sales():
    df = pd.read_parquet(OUTPUT_DIR / "fact_sales.parquet")
    df["order_date"] = pd.to_datetime(df["order_date"])
    return df


@st.cache_data
def load_rfm():
    return pd.read_csv(OUTPUT_DIR / "rfm_table_with_clusters.csv")


@st.cache_data
def load_stores():
    return pd.read_csv(OUTPUT_DIR / "stores.csv")


@st.cache_data
def load_completed_sales():
    df = load_fact_sales()
    return df[df["status"] == "completed"]


@st.cache_data
def load_promotions():
    return pd.read_csv(OUTPUT_DIR / "promotions.csv", parse_dates=["start_date", "end_date"])


@st.cache_data
def load_flagged_sales():
    return flag_promotion_orders(load_completed_sales(), load_promotions())