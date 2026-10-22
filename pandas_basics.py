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


customers = pd.read_sql("SELECT * FROM customers", engine)
products = pd.read_sql("SELECT * FROM products", engine)
categories = pd.read_sql("SELECT * FROM categories", engine)
orders = pd.read_sql("SELECT * FROM orders", engine)
order_items = pd.read_sql("SELECT * FROM order_items", engine)
payments = pd.read_sql("SELECT * FROM payments", engine)



customers_sofia = customers[customers["city"] == "Sofia"]

cancelled_orders = orders[orders["status"] == "cancelled"]

expensive_products = products[products["price"] > 100]

orders["order_date"] = pd.to_datetime(orders["order_date"])
recent_completed_orders = orders[
    (orders["status"] == "completed")
    & (orders["order_date"] >= pd.Timestamp.now() - pd.DateOffset(months=6))
]

top5_products_by_price = products.sort_values("price", ascending=False).head(5)

orders_by_date_desc = orders.sort_values("order_date", ascending=False)


order_items_with_products = order_items.merge(
    products, on="product_id", how="inner"
)

order_items_full = order_items_with_products.merge(
    categories, on="category_id", how="left"
)

orders_with_customers = orders.merge(
    customers, on="customer_id", how="left", suffixes=("_order", "_customer")
)


order_items["line_revenue"] = order_items["quantity"] * order_items["unit_price"]
revenue_per_product = (
    order_items.groupby("product_id")["line_revenue"].sum().reset_index(name="total_revenue")
)

order_items_full["line_revenue"] = (
    order_items_full["quantity"] * order_items_full["unit_price"]
)
revenue_per_category = (
    order_items_full.groupby("category_name")["line_revenue"]
    .sum()
    .sort_values(ascending=False)
    .reset_index(name="total_revenue")
)


orders_per_customer = orders.groupby("customer_id")["order_id"].count().reset_index(
    name="order_count"
)
paid_per_customer = payments.merge(
    orders[["order_id", "customer_id"]], on="order_id", how="left"
).groupby("customer_id")["amount"].sum().reset_index(name="total_paid")


if __name__ == "__main__":
    print("Customers from Sofia:", len(customers_sofia))
    print("Cancelled orders:", len(cancelled_orders))
    print("Products above 100:", len(expensive_products))
    print("Completed orders, last 6 months:", len(recent_completed_orders))
    print("\nTop 5 most expensive products:")
    print(top5_products_by_price[["product_name", "price"]])
    print("\nRevenue per category:")
    print(revenue_per_category)
    print("\nTop 5 customers by total paid:")
    print(paid_per_customer.sort_values("total_paid", ascending=False).head())