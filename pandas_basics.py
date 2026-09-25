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

# =====================================================================
# 1. Load tables into DataFrames
# =====================================================================

customers = pd.read_sql("SELECT * FROM customers", engine)
products = pd.read_sql("SELECT * FROM products", engine)
categories = pd.read_sql("SELECT * FROM categories", engine)
orders = pd.read_sql("SELECT * FROM orders", engine)
order_items = pd.read_sql("SELECT * FROM order_items", engine)
payments = pd.read_sql("SELECT * FROM payments", engine)

# =====================================================================
# 2. Filtering
# =====================================================================

# Customers from Sofia
customers_sofia = customers[customers["city"] == "Sofia"]

# Cancelled orders
cancelled_orders = orders[orders["status"] == "cancelled"]

# Products priced above 100
expensive_products = products[products["price"] > 100]

# Combined condition: completed orders placed in the last 6 months
orders["order_date"] = pd.to_datetime(orders["order_date"])
recent_completed_orders = orders[
    (orders["status"] == "completed")
    & (orders["order_date"] >= pd.Timestamp.now() - pd.DateOffset(months=6))
]

# =====================================================================
# 3. Sorting
# =====================================================================

# Top 5 most expensive products
top5_products_by_price = products.sort_values("price", ascending=False).head(5)

# Orders sorted by date, most recent first
orders_by_date_desc = orders.sort_values("order_date", ascending=False)

# =====================================================================
# 4. Merge / join
# =====================================================================

# order_items + products: attach product name/category to each line item
order_items_with_products = order_items.merge(
    products, on="product_id", how="inner"
)

# order_items + products + categories, chained
order_items_full = order_items_with_products.merge(
    categories, on="category_id", how="left"
)

# orders + customers: attach customer info to each order (LEFT JOIN,
# keeps orders even if a customer record were missing)
orders_with_customers = orders.merge(
    customers, on="customer_id", how="left", suffixes=("_order", "_customer")
)

# =====================================================================
# 5. Groupby
# =====================================================================

# Total revenue per product (quantity * unit_price at time of sale)
order_items["line_revenue"] = order_items["quantity"] * order_items["unit_price"]
revenue_per_product = (
    order_items.groupby("product_id")["line_revenue"].sum().reset_index(name="total_revenue")
)

# Total revenue per category (needs the merged table from step 4)
order_items_full["line_revenue"] = (
    order_items_full["quantity"] * order_items_full["unit_price"]
)
revenue_per_category = (
    order_items_full.groupby("category_name")["line_revenue"]
    .sum()
    .sort_values(ascending=False)
    .reset_index(name="total_revenue")
)

# Number of orders and total paid per customer
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