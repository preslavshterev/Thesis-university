import os
import time

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "diploma_project")

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")


def compare_loop_vs_vectorized(order_items):
    prices = order_items["unit_price"].to_numpy()
    quantities = order_items["quantity"].to_numpy()

    start = time.time()
    totals_loop = [p * q for p, q in zip(prices, quantities)]
    loop_time = time.time() - start

    start = time.time()
    totals_vectorized = prices * quantities
    vector_time = time.time() - start

    assert list(totals_loop) == list(totals_vectorized), "Mismatch between loop and vectorized results"

    print(f"Loop time: {loop_time:.6f}s | Vectorized time: {vector_time:.6f}s")
    return totals_vectorized



def summarize_revenue(revenue):
    print("Mean order line value:", np.mean(revenue))
    print("Median order line value:", np.median(revenue))
    print("Std deviation:", np.std(revenue))
    print("Min / Max:", np.min(revenue), "/", np.max(revenue))
    print("25th/75th percentile:", np.percentile(revenue, [25, 75]))



def add_is_expensive_flag(products):
    products = products.copy()
    prices = products["price"].to_numpy()
    products["is_expensive"] = np.where(prices > 150, "expensive", "affordable")
    return products



def add_margin_category(products):
    products = products.copy()
    products["profit_per_unit"] = products["price"] - products["cost"]
    products["margin_pct"] = (products["profit_per_unit"] / products["price"]) * 100

    conditions = [
        products["margin_pct"] >= 50,
        products["margin_pct"] >= 30,
        products["margin_pct"] >= 10,
    ]
    choices = ["high_margin", "medium_margin", "low_margin"]
    products["margin_category"] = np.select(conditions, choices, default="very_low_margin")

    return products



def add_discounted_price(products):
    products = products.copy()
    prices = products["price"].to_numpy()

    discount_rates = np.where(prices > 200, 0.10, 0.05)
    products["discounted_price"] = prices * (1 - discount_rates)

    return products


if __name__ == "__main__":
    order_items = pd.read_sql("SELECT * FROM order_items", engine)
    products = pd.read_sql("SELECT * FROM products", engine)

    print("=== LOOP VS VECTORIZED ===")
    revenue = compare_loop_vs_vectorized(order_items)

    print("\n=== REVENUE STATISTICS ===")
    summarize_revenue(revenue)

    print("\n=== PRODUCTS: is_expensive (np.where) ===")
    products = add_is_expensive_flag(products)
    print(products[["product_name", "price", "is_expensive"]].head())

    print("\n=== PRODUCTS: margin_category (np.select) ===")
    products = add_margin_category(products)
    print(products[["product_name", "margin_pct", "margin_category"]].head())
    print(products["margin_category"].value_counts())

    print("\n=== PRODUCTS: discounted_price (broadcasting) ===")
    products = add_discounted_price(products)
    print(products[["product_name", "price", "discounted_price"]].head())