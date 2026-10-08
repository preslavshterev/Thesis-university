import plotly.express as px
import streamlit as st

from customers import describe_clusters
from data_access import load_rfm
from formatting import CURRENCY_SYMBOL

BAR_COLOR = "#2E6F9E"
MONEY_FORMAT = f"{CURRENCY_SYMBOL}%.2f"

st.title("Customers")

try:
    rfm = load_rfm()
except FileNotFoundError as error:
    st.error(
        f"A required data file is missing ({error}). "
        "Run etl_pipeline.py and customers.py first."
    )
    st.stop()

st.subheader("RFM segments")

segment_counts = (
    rfm["segment"].value_counts().rename_axis("segment").reset_index(name="customers")
)
fig_segments = px.bar(
    segment_counts,
    x="customers",
    y="segment",
    orientation="h",
    labels={"customers": "Customers", "segment": "Segment"},
    color_discrete_sequence=[BAR_COLOR],
)
fig_segments.update_layout(yaxis={"categoryorder": "total ascending"})
st.plotly_chart(fig_segments)

segment_summary = (
    rfm.groupby("segment")
    .agg(
        customers=("customer_id", "count"),
        avg_recency_days=("recency_days", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_monetary=("monetary", "mean"),
    )
    .round(2)
    .sort_values("customers", ascending=False)
)
st.dataframe(
    segment_summary,
    column_config={
        "avg_monetary": st.column_config.NumberColumn("Avg monetary", format=MONEY_FORMAT),
    },
)

st.subheader("K-Means clusters")

cluster_data = rfm.assign(cluster=rfm["cluster"].astype(str))
fig_clusters = px.scatter(
    cluster_data,
    x="frequency",
    y="monetary",
    color="cluster",
    category_orders={"cluster": sorted(cluster_data["cluster"].unique())},
    hover_data=["customer_id", "recency_days"],
    labels={"frequency": "Orders", "monetary": "Total spent", "cluster": "Cluster"},
)
fig_clusters.update_layout(yaxis_tickprefix=CURRENCY_SYMBOL, yaxis_tickformat=",")
st.plotly_chart(fig_clusters)

cluster_profile = describe_clusters(rfm).round(2)
cluster_profile.insert(0, "customers", rfm["cluster"].value_counts().sort_index())
st.dataframe(
    cluster_profile,
    column_config={
        "monetary": st.column_config.NumberColumn("Avg monetary", format=MONEY_FORMAT),
    },
)