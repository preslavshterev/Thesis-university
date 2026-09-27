import pandas as pd


FACT_SALES_PATH = "output/fact_sales.parquet"


# =====================================================================
# 1. Core KPI functions
# =====================================================================

def calculate_total_revenue(df):
    """Sum of line_total (quantity * unit_price) across all rows."""
    return df["line_total"].sum()


def calculate_total_profit(df):
    """Sum of (unit_price - cost) * quantity across all rows."""
    profit_per_line = (df["unit_price"] - df["cost"]) * df["quantity"]
    return profit_per_line.sum()


def calculate_order_count(df):
    """Number of distinct orders (fact_sales has one row per sold item)."""
    return df["order_id"].nunique()


def calculate_aov(df):
    """Average Order Value = total revenue / number of distinct orders."""
    revenue = calculate_total_revenue(df)
    orders = calculate_order_count(df)
    return revenue / orders if orders > 0 else 0


# =====================================================================
# 2. Summary
# =====================================================================

def generate_kpi_summary(fact_sales):
    """Compute the core KPIs on completed orders only."""
    completed = fact_sales[fact_sales["status"] == "completed"]

    return {
        "total_revenue": calculate_total_revenue(completed),
        "total_profit": calculate_total_profit(completed),
        "order_count": calculate_order_count(completed),
        "average_order_value": calculate_aov(completed),
    }


if __name__ == "__main__":
    fact_sales = pd.read_parquet(FACT_SALES_PATH)

    summary = generate_kpi_summary(fact_sales)

    print("=== CORE KPIs (completed orders only) ===")
    print(f"Total revenue:        {summary['total_revenue']:.2f}")
    print(f"Total profit:         {summary['total_profit']:.2f}")
    print(f"Order count:          {summary['order_count']}")
    print(f"Average order value:  {summary['average_order_value']:.2f}")

    print("\n=== FOR COMPARISON: all orders (including cancelled) ===")
    all_summary = {
        "total_revenue": calculate_total_revenue(fact_sales),
        "order_count": calculate_order_count(fact_sales),
    }
    print(f"Total revenue (all):  {all_summary['total_revenue']:.2f}")
    print(f"Order count (all):    {all_summary['order_count']}")