import io

import pandas as pd
from openpyxl.utils import get_column_letter

from products import top_products_by_revenue
from sales import generate_kpi_summary, revenue_by_category, revenue_by_month, revenue_by_store

SALES_LINE_COLUMNS = [
    "order_id", "order_date", "product_name", "category_name",
    "store_id", "quantity", "unit_price", "line_total",
]


def sales_lines(completed):
    columns = [column for column in SALES_LINE_COLUMNS if column in completed.columns]
    return completed[columns].sort_values("order_date")


def build_report_tables(completed, stores, filter_summary):
    kpis = generate_kpi_summary(completed)
    summary = pd.DataFrame({
        "metric": ["Total revenue", "Total profit", "Orders", "Average order value"],
        "value": pd.Series([
            round(kpis["total_revenue"], 2),
            round(kpis["total_profit"], 2),
            int(kpis["order_count"]),
            round(kpis["average_order_value"], 2),
        ], dtype=object),
    })

    tables = {
        "Summary": summary,
        "Monthly revenue": revenue_by_month(completed)[["period", "line_total"]]
        .rename(columns={"line_total": "revenue"}),
        "By category": revenue_by_category(completed)
        .rename(columns={"category_name": "category", "line_total": "revenue"}),
        "By store": revenue_by_store(completed, stores)
        .rename(columns={"store_name": "store", "store_city": "city", "line_total": "revenue"}),
        "Top products": top_products_by_revenue(completed)
        .rename(columns={"product_name": "product", "line_total": "revenue"}),
        "Filters": filter_summary,
    }

    for table in tables.values():
        for column in ("revenue", "value"):
            if column in table.columns and pd.api.types.is_numeric_dtype(table[column]):
                table[column] = table[column].round(2)
    return tables


def to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8-sig")


def to_excel_bytes(tables):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for name, df in tables.items():
            df.to_excel(writer, sheet_name=name, index=False)
            sheet = writer.sheets[name]
            for position, column in enumerate(df.columns, start=1):
                longest = max([len(str(column))] + [len(str(value)) for value in df[column]])
                sheet.column_dimensions[get_column_letter(position)].width = min(longest + 2, 60)
    return buffer.getvalue()