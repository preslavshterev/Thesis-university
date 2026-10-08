import plotly.express as px
import streamlit as st

from data_access import load_flagged_sales
from filters import apply_filters, get_filtered_sales
from formatting import CURRENCY_SYMBOL, format_money
from products import (
    bottom_products_by_revenue,
    compare_promotion_effect,
    seasonal_trends_by_category,
    top_products_by_quantity,
    top_products_by_revenue,
)

BAR_COLOR = "#2E6F9E"

st.title("Products")

try:
    completed = get_filtered_sales()
    flagged = apply_filters(load_flagged_sales())
except FileNotFoundError as error:
    st.error(
        f"A required data file is missing ({error}). "
        "Run etl_pipeline.py and export_tables.py first."
    )
    st.stop()

if completed.empty:
    st.warning("No sales match the selected filters.")
    st.stop()


def horizontal_bar(data, value_column, value_label, money=False):
    fig = px.bar(
        data,
        x=value_column,
        y="product_name",
        orientation="h",
        labels={value_column: value_label, "product_name": "Product"},
        color_discrete_sequence=[BAR_COLOR],
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    if money:
        fig.update_layout(xaxis_tickprefix=CURRENCY_SYMBOL, xaxis_tickformat=",")
    return fig


tab_ranking, tab_season, tab_promo = st.tabs(["Top and bottom", "Seasonality", "Promotions"])

with tab_ranking:
    left, right = st.columns(2)
    with left:
        st.subheader("Top 10 by revenue")
        st.plotly_chart(
            horizontal_bar(top_products_by_revenue(completed), "line_total", "Revenue", money=True)
        )
    with right:
        st.subheader("Bottom 10 by revenue")
        st.plotly_chart(
            horizontal_bar(bottom_products_by_revenue(completed), "line_total", "Revenue", money=True)
        )

    st.subheader("Top 10 by units sold")
    st.plotly_chart(
        horizontal_bar(top_products_by_quantity(completed), "quantity", "Units sold")
    )

with tab_season:
    st.subheader("Revenue by category and quarter")
    pivot = seasonal_trends_by_category(completed)
    fig_season = px.imshow(
        pivot,
        text_auto=",.0f",
        aspect="auto",
        color_continuous_scale="Blues",
        labels={"x": "Quarter", "y": "Category", "color": "Revenue"},
    )
    st.plotly_chart(fig_season)

with tab_promo:
    st.subheader("Effect of promotions")
    st.caption("Products that had at least one promotion, sales during vs outside it")

    promoted_ids = flagged.loc[flagged["on_promotion"], "product_id"].unique()
    promoted_sales = flagged[flagged["product_id"].isin(promoted_ids)]

    if promoted_sales.empty:
        st.info("No promoted products found in the data.")
    else:
        effect = (
            promoted_sales.groupby("on_promotion")
            .agg(
                sales=("order_item_id", "count"),
                avg_quantity=("quantity", "mean"),
                avg_line_total=("line_total", "mean"),
            )
            .rename(index={False: "Outside promotion", True: "During promotion"})
        )

        col1, col2 = st.columns(2)
        for column, label in zip((col1, col2), ("Outside promotion", "During promotion")):
            if label in effect.index:
                row = effect.loc[label]
                column.metric(
                    f"Avg sale value, {label.lower()}",
                    format_money(row["avg_line_total"]),
                    help=f"{int(row['sales'])} sales, avg {row['avg_quantity']:.2f} units per sale",
                )

        with st.expander("Per product"):
            st.dataframe(compare_promotion_effect(flagged).round(2))