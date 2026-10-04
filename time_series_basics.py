import os

import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose

FACT_SALES_PATH = "output/fact_sales.parquet"
OUTPUT_DIR = "output"


# =====================================================================
# 1. Building continuous time series (day / week / month)
# =====================================================================

def build_daily_series(completed):
    """Total revenue per calendar day, with every day present (days
    with no sales get 0, not a missing row). This "no gaps" property
    is required by forecasting models later."""
    completed = completed.copy()
    completed["order_date"] = pd.to_datetime(completed["order_date"])

    daily = completed.set_index("order_date")["line_total"].resample("D").sum()
    return daily


def build_weekly_series(completed):
    completed = completed.copy()
    completed["order_date"] = pd.to_datetime(completed["order_date"])

    weekly = completed.set_index("order_date")["line_total"].resample("W").sum()
    return weekly


def build_monthly_series(completed):
    completed = completed.copy()
    completed["order_date"] = pd.to_datetime(completed["order_date"])

    # "MS" = Month Start, so each point is labeled with the first day
    # of its month (a common convention for monthly time series).
    monthly = completed.set_index("order_date")["line_total"].resample("MS").sum()
    return monthly


# =====================================================================
# 2. Decomposition: trend, seasonality, noise
# =====================================================================

def decompose_daily_series(daily_series, period=7):
    """Split the daily series into trend, seasonal and residual
    components. period=7 looks for a weekly pattern (e.g. weekends
    selling differently from weekdays), which is the most natural
    seasonality to expect in daily retail data."""
    decomposition = seasonal_decompose(daily_series, model="additive", period=period)
    return decomposition


def plot_decomposition(decomposition, output_path):
    fig = decomposition.plot()
    fig.set_size_inches(12, 8)
    fig.tight_layout()
    fig.savefig(output_path)


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    fact_sales = pd.read_parquet(FACT_SALES_PATH)
    completed = fact_sales[fact_sales["status"] == "completed"]

    print("=== BUILDING TIME SERIES ===")
    daily = build_daily_series(completed)
    weekly = build_weekly_series(completed)
    monthly = build_monthly_series(completed)

    print(f"Daily series:   {len(daily)} days, from {daily.index.min().date()} to {daily.index.max().date()}")
    print(f"Weekly series:  {len(weekly)} weeks")
    print(f"Monthly series: {len(monthly)} months")

    daily.to_csv(os.path.join(OUTPUT_DIR, "daily_revenue_series.csv"), header=["revenue"])
    weekly.to_csv(os.path.join(OUTPUT_DIR, "weekly_revenue_series.csv"), header=["revenue"])
    monthly.to_csv(os.path.join(OUTPUT_DIR, "monthly_revenue_series.csv"), header=["revenue"])
    print("\nSaved daily/weekly/monthly revenue series to the output/ folder.")

    print("\n=== DECOMPOSING THE DAILY SERIES (trend / weekly seasonality / noise) ===")
    decomposition = decompose_daily_series(daily, period=7)

    print("First 5 trend values (NaN at the edges is expected -- the")
    print("trend needs a few days of context on both sides to compute):")
    print(decomposition.trend.head())

    print("\nFirst 7 seasonal values (one full weekly cycle):")
    print(decomposition.seasonal.head(7))

    plot_decomposition(decomposition, os.path.join(OUTPUT_DIR, "daily_decomposition.png"))
    print(f"\nDecomposition plot saved to {OUTPUT_DIR}/daily_decomposition.png")