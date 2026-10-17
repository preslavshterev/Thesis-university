import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "diploma_project")

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")




def add_date_features(orders):
    orders = orders.copy()
    orders["order_date"] = pd.to_datetime(orders["order_date"])

    orders["order_year"] = orders["order_date"].dt.year
    orders["order_month"] = orders["order_date"].dt.month
    orders["order_week"] = orders["order_date"].dt.isocalendar().week
    orders["order_day_of_week"] = orders["order_date"].dt.day_name()
    orders["order_quarter"] = orders["order_date"].dt.quarter

    return orders


def add_price_tier(products):
    products = products.copy()

    price_bins = [0, 50, 150, 300, float("inf")]
    price_labels = ["budget", "mid_range", "premium", "luxury"]
    products["price_tier"] = pd.cut(
        products["price"], bins=price_bins, labels=price_labels
    )

    return products


def add_product_profit_features(products):
    products = products.copy()

    products["profit_per_unit"] = products["price"] - products["cost"]
    products["margin_pct"] = (products["profit_per_unit"] / products["price"]) * 100

    return products


def add_order_item_line_total(order_items):
    order_items = order_items.copy()
    order_items["line_total"] = order_items["quantity"] * order_items["unit_price"]
    return order_items


def add_customer_tenure_features(customers):
    customers = customers.copy()
    customers["registration_date"] = pd.to_datetime(customers["registration_date"])

    customers["customer_tenure_days"] = (
        pd.Timestamp.now() - customers["registration_date"]
    ).dt.days
    customers["is_new_customer"] = customers["customer_tenure_days"] <= 90

    return customers


def enrich_all(customers, products, orders, order_items):
    customers_enriched = add_customer_tenure_features(customers)
    products_enriched = add_product_profit_features(add_price_tier(products))
    orders_enriched = add_date_features(orders)
    order_items_enriched = add_order_item_line_total(order_items)

    return customers_enriched, products_enriched, orders_enriched, order_items_enriched


if __name__ == "__main__":
    customers = pd.read_sql("SELECT * FROM customers", engine)
    products = pd.read_sql("SELECT * FROM products", engine)
    orders = pd.read_sql("SELECT * FROM orders", engine)
    order_items = pd.read_sql("SELECT * FROM order_items", engine)

    customers, products, orders, order_items = enrich_all(
        customers, products, orders, order_items
    )

    print("Customers with new columns:")
    print(customers[["customer_id", "customer_tenure_days", "is_new_customer"]].head())

    print("\nProducts with new columns:")
    print(products[["product_name", "price", "price_tier", "profit_per_unit", "margin_pct"]].head())

    print("\nOrders with new columns:")
    print(orders[["order_id", "order_year", "order_month", "order_week", "order_day_of_week", "order_quarter"]].head())

    print("\nOrder items with new columns:")
    print(order_items[["order_item_id", "quantity", "unit_price", "line_total"]].head())

    print("\nOrders per day of week:")
    print(orders["order_day_of_week"].value_counts())

    print("\nProducts per price tier:")
    print(products["price_tier"].value_counts())