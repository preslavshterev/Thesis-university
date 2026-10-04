import os

import matplotlib.pyplot as plt
import pandas as pd

COMPARISON_PATH = "output/arima_test_forecast.csv"
OUTPUT_DIR = "output"


# =====================================================================
# 1. Load the actual-vs-forecast table from Day 25
# =====================================================================

def load_comparison(path):
    return pd.read_csv(path, index_col=0, parse_dates=True)


# =====================================================================
# 2. Error metrics
# =====================================================================

def calculate_mae(actual, forecast):
    """Mean Absolute Error: average of |actual - forecast|, in the
    same units as the data itself (here, currency)."""
    return (actual - forecast).abs().mean()


def calculate_rmse(actual, forecast):
    """Root Mean Squared Error: squares the errors before averaging
    (which punishes large mistakes disproportionately more than small
    ones), then takes the square root to return to the original
    units. RMSE is always >= MAE; a much larger RMSE than MAE signals
    that a few large errors dominate, rather than the error being
    evenly spread out."""
    return ((actual - forecast) ** 2).mean() ** 0.5


def calculate_mape(actual, forecast):
    """Mean Absolute Percentage Error: the error expressed as a
    percentage of the actual value, which makes it comparable across
    series of different scales. Days where actual == 0 are excluded,
    since dividing by zero would be undefined -- this is a well-known
    limitation of MAPE on data with zero/near-zero values, which is
    common in retail (days with no sales)."""
    non_zero_mask = actual != 0
    excluded_days = (~non_zero_mask).sum()

    percentage_errors = (actual[non_zero_mask] - forecast[non_zero_mask]).abs() / actual[non_zero_mask]
    mape = percentage_errors.mean() * 100

    return mape, excluded_days


# =====================================================================
# 3. Visualizing the daily error
# =====================================================================

def plot_daily_errors(comparison, output_path):
    """A bar chart of the absolute error on each test day -- shows
    whether the mistakes are spread evenly or concentrated on a few
    unusually high-demand days."""
    absolute_error = (comparison["actual"] - comparison["forecast"]).abs()

    plt.figure(figsize=(12, 5))
    plt.bar(absolute_error.index.strftime("%Y-%m-%d"), absolute_error.values)
    plt.xticks(rotation=45, ha="right")
    plt.title("Absolute forecast error per day (test period)")
    plt.ylabel("Absolute error")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    comparison = load_comparison(COMPARISON_PATH)
    actual = comparison["actual"]
    forecast = comparison["forecast"]

    mae = calculate_mae(actual, forecast)
    rmse = calculate_rmse(actual, forecast)
    mape, excluded_days = calculate_mape(actual, forecast)

    print("=== FORECAST ACCURACY METRICS (test period) ===")
    print(f"MAE:  {mae:.2f}")
    print(f"RMSE: {rmse:.2f}")
    print(f"MAPE: {mape:.2f}% (excluded {excluded_days} day(s) with actual = 0)")

    # For context: how big is the error relative to the typical day?
    mean_actual = actual.mean()
    print(f"\nFor context -- mean actual revenue over the test period: {mean_actual:.2f}")
    print(f"MAE as a percentage of the mean actual value: {(mae / mean_actual) * 100:.1f}%")

    plot_daily_errors(comparison, os.path.join(OUTPUT_DIR, "forecast_errors.png"))
    print(f"\nDaily error chart saved to {OUTPUT_DIR}/forecast_errors.png")