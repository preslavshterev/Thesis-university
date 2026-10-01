import os

import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "diploma_project")

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")

FACT_SALES_PATH = "output/fact_sales.parquet"
OUTPUT_DIR = "output"


# =====================================================================
# 1. Best / worst selling products
# =====================================================================

def top_products_by_revenue(completed, n=10):
    return (
        completed.groupby("product_name")["line_total"]
        .sum()
        .sort_values(ascending=False)
        .head(n)
        .reset_index()
    )


def bottom_products_by_revenue(completed, n=10):
    return (
        completed.groupby("product_name")["line_total"]
        .sum()
        .sort_values(ascending=True)
        .head(n)
        .reset_index()
    )


def top_products_by_quantity(completed, n=10):
    return (
        completed.groupby("product_name")["quantity"]
        .sum()
        .sort_values(ascending=False)
        .head(n)
        .reset_index()
    )


# =====================================================================
# 2. Seasonal trends by category
# =====================================================================

def seasonal_trends_by_category(completed):
    """Pivot table: total revenue per category, per quarter. Useful to
    spot categories that sell disproportionately well in a given
    season (e.g. higher electronics sales in Q4)."""
    pivot = completed.pivot_table(
        index="category_name",
        columns="order_quarter",
        values="line_total",
        aggfunc="sum",
        fill_value=0,
    )
    pivot.columns = [f"Q{q}" for q in pivot.columns]
    return pivot


def plot_seasonal_trends(pivot, output_path):
    pivot.plot(kind="bar", figsize=(12, 6))
    plt.title("Revenue by category and quarter")
    plt.ylabel("Revenue")
    plt.xticks(rotation=45, ha="right")
    plt.legend(title="Quarter")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


# =====================================================================
# 3. Effect of promotions
# =====================================================================

def load_promotions():
    """Promotions are not part of fact_sales, so they are loaded
    directly from MySQL."""
    promotions = pd.read_sql("SELECT * FROM promotions", engine)
    promotions["start_date"] = pd.to_datetime(promotions["start_date"])
    promotions["end_date"] = pd.to_datetime(promotions["end_date"])
    return promotions


def flag_promotion_orders(completed, promotions):
    """Mark each sale as having happened during an active promotion for
    that product, by joining on product_id and then checking whether
    the order date falls inside the promotion's [start_date, end_date]
    range (a date-range join, not a simple key match)."""
    completed = completed.copy()
    completed["order_date"] = pd.to_datetime(completed["order_date"])

    merged = completed.merge(promotions, on="product_id", how="left", suffixes=("", "_promo"))

    in_promotion = (
        (merged["order_date"] >= merged["start_date"])
        & (merged["order_date"] <= merged["end_date"])
    )

    # A product can have more than one promotion in the data, which
    # would duplicate rows via the merge above. Collapse back down to
    # one row per original sale with a single True/False flag.
    merged["on_promotion"] = in_promotion.fillna(False)
    flag_per_item = merged.groupby("order_item_id")["on_promotion"].any()

    completed["on_promotion"] = completed["order_item_id"].map(flag_per_item).fillna(False)
    return completed


def compare_promotion_effect(flagged):
    """For products that were ever promoted, compare average quantity
    and revenue per sale during the promotion vs outside of it."""
    promoted_product_ids = flagged.loc[flagged["on_promotion"], "product_id"].unique()
    promoted_only = flagged[flagged["product_id"].isin(promoted_product_ids)]

    return (
        promoted_only.groupby(["product_name", "on_promotion"])
        .agg(avg_quantity=("quantity", "mean"), avg_line_total=("line_total", "mean"), sales_count=("order_item_id", "count"))
        .reset_index()
    )


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    fact_sales = pd.read_parquet(FACT_SALES_PATH)
    completed = fact_sales[fact_sales["status"] == "completed"]

    print("=== TOP 10 PRODUCTS BY REVENUE ===")
    print(top_products_by_revenue(completed))

    print("\n=== BOTTOM 10 PRODUCTS BY REVENUE ===")
    print(bottom_products_by_revenue(completed))

    print("\n=== TOP 10 PRODUCTS BY QUANTITY SOLD ===")
    print(top_products_by_quantity(completed))

    print("\n=== SEASONAL TRENDS (REVENUE BY CATEGORY AND QUARTER) ===")
    pivot = seasonal_trends_by_category(completed)
    print(pivot)
    plot_seasonal_trends(pivot, os.path.join(OUTPUT_DIR, "seasonal_trends.png"))

    print("\n=== PROMOTION EFFECT ===")
    promotions = load_promotions()
    flagged = flag_promotion_orders(completed, promotions)
    effect = compare_promotion_effect(flagged)
    print(effect)

    print(f"\nChart saved to '{OUTPUT_DIR}/seasonal_trends.png'.")