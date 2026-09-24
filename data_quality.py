"""
Day 10 -- ETL: detecting missing values, duplicates and invalid records
(data quality validation).

Loads the core tables from the diploma_project MySQL database and runs
a set of data-quality checks on them: missing values per column,
duplicate rows, and business-rule violations (negative prices, orders
with future dates, etc.).

Requires a running MySQL instance with the schema from schema.sql and
data from generate_data.py, plus a .env file with:
    DB_USER=...
    DB_PASSWORD=...
    DB_HOST=localhost
    DB_NAME=diploma_project
"""

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
# 1. Missing values
# =====================================================================

def check_missing_values(df, table_name):
    """Print and return the count of missing (NaN/None) values per column."""
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if missing.empty:
        print(f"[{table_name}] No missing values.")
    else:
        print(f"[{table_name}] Missing values per column:")
        print(missing)
    return missing


# =====================================================================
# 2. Duplicates
# =====================================================================

def check_duplicates(df, table_name, subset=None):
    """Print and return rows that are duplicated (optionally on a subset of columns)."""
    dup_count = df.duplicated(subset=subset).sum()
    label = f"on {subset}" if subset else "on full row"
    print(f"[{table_name}] Duplicate rows ({label}): {dup_count}")
    return df[df.duplicated(subset=subset, keep=False)]


# =====================================================================
# 3. Business-rule validation (invalid records)
# =====================================================================

def check_invalid_records(customers, products, orders, order_items):
    """Check a set of business rules that raw data may violate even though
    it satisfies the database's own constraints."""
    issues = {}

    # Zero or negative prices
    issues["negative_prices"] = products[products["price"] <= 0]

    # Products sold at a loss (cost higher than the selling price)
    issues["cost_above_price"] = products[products["cost"] > products["price"]]

    # Orders dated in the future (a sign of bad data entry/generation)
    orders = orders.copy()
    orders["order_date"] = pd.to_datetime(orders["order_date"])
    issues["future_orders"] = orders[orders["order_date"] > pd.Timestamp.now()]

    # Order items with non-positive quantity
    issues["invalid_quantity"] = order_items[order_items["quantity"] <= 0]

    # Emails without an "@" (simple sanity check, not full validation)
    issues["invalid_email"] = customers[~customers["email"].str.contains("@", na=False)]

    for name, df in issues.items():
        print(f"{name}: {len(df)} record(s)")

    return issues


# =====================================================================
# 4. Full data-quality report
# =====================================================================

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