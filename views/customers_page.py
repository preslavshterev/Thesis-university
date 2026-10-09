import plotly.express as px
import streamlit as st

from customers import describe_clusters
from data_access import load_rfm
from formatting import CURRENCY_SYMBOL
from ui import CATEGORY_COLORS, PRIMARY, card, chart_card, page_header, style_chart

MONEY_FORMAT = f"{CURRENCY_SYMBOL}%.2f"

page_header(
    "Customers",
    "RFM segments and K-Means clusters, calculated on the whole sales history (sidebar filters do not apply).",
)

try:
    rfm = load_rfm()
except FileNotFoundError as error:
    st.error(
        f"A required data file is missing ({error}). "
        "Run etl_pipeline.py and customers.py first."
    )
    st.stop()

segment_counts = (
    rfm["segment"].value_counts().rename_axis("segment").reset_index(name="customers")
)
fig_segments = px.bar(
    segment_counts, x="customers", y="segment", orientation="h",
    labels={"customers": "Customers", "segment": "Segment"},
    color_discrete_sequence=[PRIMARY],
)
fig_segments.update_layout(yaxis={"categoryorder": "total ascending"})

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

left, right = st.columns(2)
with left:
    chart_card("RFM segments", style_chart(fig_segments, height=340))
with right:
    with card("Segment profile"):
        st.subheader("Segment profile")
        st.dataframe(
            segment_summary,
            column_config={
                "avg_monetary": st.column_config.NumberColumn("Avg monetary", format=MONEY_FORMAT),
            },
        )

cluster_data = rfm.assign(cluster=rfm["cluster"].astype(str))
fig_clusters = px.scatter(
    cluster_data, x="frequency", y="monetary", color="cluster",
    category_orders={"cluster": sorted(cluster_data["cluster"].unique())},
    color_discrete_sequence=CATEGORY_COLORS,
    hover_data=["customer_id", "recency_days"],
    labels={"frequency": "Orders", "monetary": "Total spent", "cluster": "Cluster"},
)

cluster_profile = describe_clusters(rfm).round(2)
cluster_profile.insert(0, "customers", rfm["cluster"].value_counts().sort_index())

left, right = st.columns(2)
with left:
    chart_card("K-Means clusters", style_chart(fig_clusters, money_axis="y", height=340))
with right:
    with card("Cluster profile"):
        st.subheader("Cluster profile")
        st.dataframe(
            cluster_profile,
            column_config={
                "monetary": st.column_config.NumberColumn("Avg monetary", format=MONEY_FORMAT),
            },
        )