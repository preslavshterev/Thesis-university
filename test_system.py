import io
import os
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from auth import hash_password, verify_password
from customers import OPTIMAL_K
from filters import filter_sales
from inventory import build_inventory_table
from products import flag_promotion_orders
from reports import build_report_tables, sales_lines, to_excel_bytes
from sales import (
    calculate_total_revenue,
    generate_kpi_summary,
    revenue_by_category,
    revenue_by_month,
    revenue_by_store,
)

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
TOLERANCE = 0.01

REQUIRED_SALES_COLUMNS = [
    "order_item_id", "order_id", "product_id", "customer_id", "store_id",
    "category_name", "product_name", "quantity", "unit_price", "line_total",
    "order_date", "status",
]


class Skip(Exception):
    pass


def read_csv(name, **kwargs):
    return pd.read_csv(OUTPUT_DIR / name, **kwargs)


def read_fact_sales():
    return pd.read_parquet(OUTPUT_DIR / "fact_sales.parquet")


def read_completed_sales():
    sales = read_fact_sales()
    return sales[sales["status"] == "completed"]


def assert_close(actual, expected, label, tolerance=TOLERANCE):
    assert abs(actual - expected) <= tolerance, f"{label}: {actual:.2f} vs {expected:.2f}"


def test_fact_sales_integrity():
    sales = read_fact_sales()

    missing = [column for column in REQUIRED_SALES_COLUMNS if column not in sales.columns]
    assert not missing, f"missing columns: {missing}"

    nulls = sales[REQUIRED_SALES_COLUMNS].isna().sum()
    nulls = nulls[nulls > 0]
    assert nulls.empty, f"null values found: {nulls.to_dict()}"

    assert sales["order_item_id"].is_unique, "duplicate order_item_id"
    assert (sales["quantity"] > 0).all(), "non-positive quantity"
    assert (sales["unit_price"] > 0).all(), "non-positive unit price"
    assert np.allclose(sales["line_total"], sales["quantity"] * sales["unit_price"]), "line_total mismatch"
    assert set(sales["status"]) <= {"completed", "cancelled", "pending"}, "unexpected status"


def test_revenue_breakdowns_add_up():
    completed = read_completed_sales()
    stores = read_csv("stores.csv")
    total = calculate_total_revenue(completed)

    assert_close(revenue_by_month(completed)["line_total"].sum(), total, "by month")
    assert_close(revenue_by_category(completed)["line_total"].sum(), total, "by category")
    assert_close(revenue_by_store(completed, stores)["line_total"].sum(), total, "by store")


def test_kpi_relations():
    sales = read_fact_sales()
    kpis = generate_kpi_summary(sales)
    total = calculate_total_revenue(sales[sales["status"] == "completed"])

    assert_close(kpis["total_revenue"], total, "KPI revenue")
    assert_close(kpis["average_order_value"] * kpis["order_count"], total, "AOV x orders")
    assert 0 < kpis["total_profit"] < kpis["total_revenue"], "profit outside 0..revenue"


def test_time_series_totals():
    total = calculate_total_revenue(read_completed_sales())

    for name in ("daily", "weekly", "monthly"):
        series = read_csv(f"{name}_revenue_series.csv", index_col=0, parse_dates=True)["revenue"]
        assert_close(series.sum(), total, f"{name} series")

    daily = read_csv("daily_revenue_series.csv", index_col=0, parse_dates=True)["revenue"]
    gaps = daily.index.to_series().diff().dropna()
    assert (gaps == pd.Timedelta(days=1)).all(), "daily series has missing days"


def test_rfm_table():
    completed = read_completed_sales()
    rfm = read_csv("rfm_table_with_clusters.csv")

    assert rfm["customer_id"].is_unique, "duplicate customers"
    assert len(rfm) == completed["customer_id"].nunique(), "customer count mismatch"
    assert_close(rfm["monetary"].sum(), calculate_total_revenue(completed), "RFM monetary")
    assert rfm["frequency"].sum() == completed["order_id"].nunique(), "RFM frequency mismatch"

    for column in ("R_score", "F_score", "M_score"):
        assert rfm[column].between(1, 5).all(), f"{column} outside 1..5"
    assert rfm["segment"].notna().all(), "customer without segment"
    assert sorted(rfm["cluster"].unique()) == list(range(OPTIMAL_K)), "unexpected cluster ids"


def test_inventory_table():
    inventory = read_csv("inventory.csv")
    products = read_csv("products.csv")
    stores = read_csv("stores.csv")
    categories = read_csv("categories.csv")

    assert not inventory.duplicated(["product_id", "store_id"]).any(), "duplicate product-store rows"
    assert (inventory["quantity_available"] >= 0).all(), "negative stock"
    assert len(inventory) == len(products) * len(stores), "inventory is not product x store"

    table = build_inventory_table(inventory, products, stores, categories)
    assert len(table) == len(inventory), "merge changed the row count"
    assert table["stock_value"].notna().all(), "stock value missing"


def test_promotion_flag_keeps_rows():
    completed = read_completed_sales()
    promotions = read_csv("promotions.csv", parse_dates=["start_date", "end_date"])

    assert (promotions["start_date"] <= promotions["end_date"]).all(), "promotion ends before it starts"

    flagged = flag_promotion_orders(completed, promotions)
    assert len(flagged) == len(completed), "flagging changed the row count"
    assert flagged["order_item_id"].is_unique, "flagging duplicated sales"


def test_filter_logic():
    stores = pd.DataFrame({"store_id": [1, 2], "store_name": ["A", "B"]})
    sales = pd.DataFrame({
        "order_date": pd.to_datetime(["2025-01-01 08:00", "2025-01-31 23:30", "2025-02-01 00:10"]),
        "store_id": [1, 2, 1],
        "category_name": ["X", "Y", "X"],
    })
    full = (date(2025, 1, 1), date(2025, 2, 1))

    def run(period=full, store_names=("A", "B"), categories=("X", "Y")):
        return filter_sales(sales, stores, period, list(store_names), list(categories))

    assert len(run()) == 3
    assert len(run(period=(date(2025, 1, 1), date(2025, 1, 31)))) == 2, "last day must be included"
    assert len(run(store_names=("B",))) == 1
    assert len(run(categories=("X",))) == 2
    assert run(store_names=()).empty
    assert len(run(period=(date(2025, 1, 31),))) == 1, "single date must mean one day"


def test_report_tables():
    completed = read_completed_sales()
    stores = read_csv("stores.csv")
    total = calculate_total_revenue(completed)
    filter_summary = pd.DataFrame({"filter": ["Period"], "value": ["all"]})

    tables = build_report_tables(completed, stores, filter_summary)
    assert_close(float(tables["Summary"]["value"].iloc[0]), total, "report summary")
    for name in ("Monthly revenue", "By category", "By store"):
        tolerance = 0.005 * len(tables[name]) + TOLERANCE
        assert_close(tables[name]["revenue"].sum(), total, name, tolerance)

    workbook = pd.read_excel(io.BytesIO(to_excel_bytes(tables)), sheet_name=None)
    assert set(workbook) == set(tables), "Excel sheets differ from report tables"

    personal = {"email", "phone", "first_name", "last_name"}
    assert not personal & set(sales_lines(completed).columns), "personal data in sales export"


def test_password_hashing():
    stored = hash_password("test-password")

    assert verify_password("test-password", stored)
    assert not verify_password("other-password", stored)
    assert not verify_password("test-password", "malformed")
    assert hash_password("test-password") != stored, "salt must differ between hashes"


def test_database_matches_files():
    try:
        from dotenv import load_dotenv
        from sqlalchemy import create_engine, text
    except ImportError as error:
        raise Skip(f"database libraries missing ({error.name})")

    load_dotenv()
    url = "mysql+pymysql://{}:{}@{}/{}".format(
        os.getenv("DB_USER"), os.getenv("DB_PASSWORD"),
        os.getenv("DB_HOST", "localhost"), os.getenv("DB_NAME", "diploma_project"),
    )
    queries = {
        "revenue": """SELECT SUM(oi.quantity * oi.unit_price) FROM order_items oi
                      JOIN orders o ON o.order_id = oi.order_id WHERE o.status = 'completed'""",
        "orders": "SELECT COUNT(*) FROM orders WHERE status = 'completed'",
        "customers": "SELECT COUNT(DISTINCT customer_id) FROM orders WHERE status = 'completed'",
    }

    try:
        with create_engine(url).connect() as connection:
            database = {name: connection.execute(text(sql)).scalar() for name, sql in queries.items()}
    except Exception as error:
        raise Skip(f"database not reachable ({type(error).__name__})")

    completed = read_completed_sales()
    assert_close(float(database["revenue"]), calculate_total_revenue(completed), "database vs files revenue")
    assert int(database["orders"]) == completed["order_id"].nunique(), "order count differs from database"
    assert int(database["customers"]) == completed["customer_id"].nunique(), "customer count differs from database"


TESTS = [function for name, function in list(globals().items()) if name.startswith("test_")]


def main():
    passed = failed = skipped = 0

    for test in TESTS:
        try:
            test()
        except Skip as reason:
            skipped += 1
            print(f"SKIP  {test.__name__}: {reason}")
        except Exception as error:
            failed += 1
            print(f"FAIL  {test.__name__}: {error!r}")
        else:
            passed += 1
            print(f"PASS  {test.__name__}")

    print(f"\n{passed} passed, {failed} failed, {skipped} skipped")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()