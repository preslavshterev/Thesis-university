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
# 1. Revenue trend over time (by month)
# =====================================================================

def revenue_by_month(completed):
    monthly = completed.groupby(["order_year", "order_month"])["line_total"].sum().reset_index()
    monthly["period"] = (
        monthly["order_year"].astype(str) + "-" + monthly["order_month"].astype(str).str.zfill(2)
    )
    monthly = monthly.sort_values(["order_year", "order_month"])
    return monthly


def plot_monthly_revenue(monthly, output_path):
    plt.figure(figsize=(12, 5))
    plt.plot(monthly["period"], monthly["line_total"], marker="o")
    plt.xticks(rotation=45)
    plt.title("Monthly revenue")
    plt.ylabel("Revenue")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


# =====================================================================
# 2. Revenue by category
# =====================================================================

def revenue_by_category(completed):
    return (
        completed.groupby("category_name")["line_total"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )


def plot_revenue_by_category(by_category, output_path):
    plt.figure(figsize=(10, 5))
    plt.bar(by_category["category_name"], by_category["line_total"])
    plt.xticks(rotation=45, ha="right")
    plt.title("Revenue by category")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


# =====================================================================
# 3. Revenue by store / region
# =====================================================================

def revenue_by_store(completed, stores):
    # completed already has a "city" column (the customer's city, from the
    # customers merge in etl_pipeline.py). Rename the stores' city column
    # before merging so it does not collide and get suffixed to city_x/city_y.
    stores = stores.rename(columns={"city": "store_city"})
    merged = completed.merge(stores, on="store_id", how="left")
    return (
        merged.groupby(["store_name", "store_city"])["line_total"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )


def plot_revenue_by_store(by_store, output_path):
    plt.figure(figsize=(10, 5))
    plt.bar(by_store["store_name"], by_store["line_total"])
    plt.xticks(rotation=45, ha="right")
    plt.title("Revenue by store")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    fact_sales = pd.read_parquet(FACT_SALES_PATH)
    completed = fact_sales[fact_sales["status"] == "completed"]
    stores = pd.read_sql("SELECT * FROM stores", engine)

    print("=== REVENUE BY MONTH ===")
    monthly = revenue_by_month(completed)
    print(monthly[["period", "line_total"]])
    plot_monthly_revenue(monthly, os.path.join(OUTPUT_DIR, "monthly_revenue.png"))

    print("\n=== REVENUE BY CATEGORY ===")
    by_category = revenue_by_category(completed)
    print(by_category)
    plot_revenue_by_category(by_category, os.path.join(OUTPUT_DIR, "revenue_by_category.png"))

    print("\n=== REVENUE BY STORE ===")
    by_store = revenue_by_store(completed, stores)
    print(by_store)
    plot_revenue_by_store(by_store, os.path.join(OUTPUT_DIR, "revenue_by_store.png"))

    print(f"\nCharts saved to the '{OUTPUT_DIR}/' folder.")