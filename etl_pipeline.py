import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

from data_quality import run_data_quality_report
from feature_engineering import enrich_all

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "diploma_project")

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")


def extract():
    customers = pd.read_sql("SELECT * FROM customers", engine)
    products = pd.read_sql("SELECT * FROM products", engine)
    categories = pd.read_sql("SELECT * FROM categories", engine)
    orders = pd.read_sql("SELECT * FROM orders", engine)
    order_items = pd.read_sql("SELECT * FROM order_items", engine)
    payments = pd.read_sql("SELECT * FROM payments", engine)
    return customers, products, categories, orders, order_items, payments


def transform(customers, products, categories, orders, order_items, payments):
    print("=== DATA QUALITY REPORT ===")
    run_data_quality_report(customers, products, categories, orders, order_items, payments)

    print("\n=== FEATURE ENGINEERING ===")
    customers, products, orders, order_items = enrich_all(
        customers, products, orders, order_items
    )

    fact_sales = (
        order_items
        .merge(orders, on="order_id", how="left")
        .merge(products, on="product_id", how="left", suffixes=("", "_product"))
        .merge(categories, on="category_id", how="left")
        .merge(customers, on="customer_id", how="left", suffixes=("", "_customer"))
    )

    return fact_sales



def load(fact_sales, output_dir="output"):
    os.makedirs(output_dir, exist_ok=True)

    parquet_path = os.path.join(output_dir, "fact_sales.parquet")
    csv_path = os.path.join(output_dir, "fact_sales.csv")

    fact_sales.to_parquet(parquet_path, index=False)
    fact_sales.to_csv(csv_path, index=False)

    print(f"Saved {len(fact_sales)} rows to {parquet_path} and {csv_path}")


def run_pipeline(output_dir="output"):
    raw = extract()
    fact_sales = transform(*raw)
    load(fact_sales, output_dir=output_dir)
    return fact_sales


if __name__ == "__main__":
    fact_sales = run_pipeline()
    print("\n=== FACT_SALES PREVIEW ===")
    print(fact_sales.head())
    print("\nColumns:", list(fact_sales.columns))