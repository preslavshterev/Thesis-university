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


def check_missing_values(df, table_name):
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if missing.empty:
        print(f"[{table_name}] No missing values.")
    else:
        print(f"[{table_name}] Missing values per column:")
        print(missing)
    return missing



def check_duplicates(df, table_name, subset=None):
    dup_count = df.duplicated(subset=subset).sum()
    label = f"on {subset}" if subset else "on full row"
    print(f"[{table_name}] Duplicate rows ({label}): {dup_count}")
    return df[df.duplicated(subset=subset, keep=False)]



def check_invalid_records(customers, products, orders, order_items):
    issues = {}

    issues["negative_prices"] = products[products["price"] <= 0]

    issues["cost_above_price"] = products[products["cost"] > products["price"]]

    orders = orders.copy()
    orders["order_date"] = pd.to_datetime(orders["order_date"])
    issues["future_orders"] = orders[orders["order_date"] > pd.Timestamp.now()]

    issues["invalid_quantity"] = order_items[order_items["quantity"] <= 0]

    issues["invalid_email"] = customers[~customers["email"].str.contains("@", na=False)]

    for name, df in issues.items():
        print(f"{name}: {len(df)} record(s)")

    return issues



def run_data_quality_report(customers, products, categories, orders, order_items, payments):
    print("=== MISSING VALUES ===")
    for name, df in [
        ("customers", customers),
        ("products", products),
        ("categories", categories),
        ("orders", orders),
        ("order_items", order_items),
        ("payments", payments),
    ]:
        check_missing_values(df, name)

    print("\n=== DUPLICATES ===")
    check_duplicates(customers, "customers", subset=["email"])
    check_duplicates(order_items, "order_items")

    print("\n=== INVALID RECORDS ===")
    issues = check_invalid_records(customers, products, orders, order_items)

    return issues


if __name__ == "__main__":
    customers = pd.read_sql("SELECT * FROM customers", engine)
    products = pd.read_sql("SELECT * FROM products", engine)
    categories = pd.read_sql("SELECT * FROM categories", engine)
    orders = pd.read_sql("SELECT * FROM orders", engine)
    order_items = pd.read_sql("SELECT * FROM order_items", engine)
    payments = pd.read_sql("SELECT * FROM payments", engine)

    run_data_quality_report(customers, products, categories, orders, order_items, payments)