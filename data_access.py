from pathlib import Path

import pandas as pd
import streamlit as st

OUTPUT_DIR = Path(__file__).resolve().parent / "output"


@st.cache_data
def load_fact_sales():
    df = pd.read_parquet(OUTPUT_DIR / "fact_sales.parquet")
    df["order_date"] = pd.to_datetime(df["order_date"])
    return df


@st.cache_data
def load_rfm():
    return pd.read_csv(OUTPUT_DIR / "rfm_table_with_clusters.csv")