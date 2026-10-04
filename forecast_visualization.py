import os

import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

DAILY_SERIES_PATH = "output/daily_revenue_series.csv"
OUTPUT_DIR = "output"
TEST_SIZE = 14
ARIMA_ORDER = (0, 0, 0)  # from Day 24's AIC search


# =====================================================================
# 1. Load and split (same as Day 25)
# =====================================================================

def load_daily_series(path):
    series = pd.read_csv(path, index_col=0, parse_dates=True)["revenue"]
    series = series.asfreq("D")
    return series


def split_train_test(series, test_size=TEST_SIZE):
    train = series.iloc[:-test_size]
    test = series.iloc[-test_size:]
    return train, test


# =====================================================================
# 2. Fit and forecast with a confidence interval
# =====================================================================

def fit_and_forecast_with_ci(train, order, steps, alpha=0.05):
    """get_forecast() (instead of forecast()) returns a results object
    carrying both the point forecast (.predicted_mean) and the
    confidence interval bounds (.conf_int()). alpha=0.05 means a 95%
    confidence interval (1 - alpha)."""
    model = ARIMA(train, order=order)
    fitted_model = model.fit()

    forecast_result = fitted_model.get_forecast(steps=steps)
    predicted_mean = forecast_result.predicted_mean
    confidence_interval = forecast_result.conf_int(alpha=alpha)

    return fitted_model, predicted_mean, confidence_interval


# =====================================================================
# 3. Plot
# =====================================================================

def plot_forecast_with_ci(train, test, predicted_mean, confidence_interval, output_path, last_n_days=60):
    recent_history = train.iloc[-last_n_days:]

    lower_bound = confidence_interval.iloc[:, 0]
    upper_bound = confidence_interval.iloc[:, 1]

    plt.figure(figsize=(12, 6))
    plt.plot(recent_history.index, recent_history.values, label="Historical revenue (train)", color="steelblue")
    plt.plot(test.index, test.values, label="Actual (test period)", color="green", marker="o")
    plt.plot(predicted_mean.index, predicted_mean.values, label="Forecast", color="orange", linestyle="--")
    plt.fill_between(
        predicted_mean.index, lower_bound, upper_bound,
        color="orange", alpha=0.2, label="95% confidence interval",
    )

    plt.title("Revenue forecast vs actual, with 95% confidence interval")
    plt.ylabel("Revenue")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    daily = load_daily_series(DAILY_SERIES_PATH)
    train, test = split_train_test(daily, test_size=TEST_SIZE)

    fitted_model, predicted_mean, confidence_interval = fit_and_forecast_with_ci(
        train, ARIMA_ORDER, steps=TEST_SIZE
    )

    print("=== FORECAST WITH 95% CONFIDENCE INTERVAL ===")
    result_table = pd.DataFrame({
        "actual": test,
        "forecast": predicted_mean,
        "lower_95": confidence_interval.iloc[:, 0],
        "upper_95": confidence_interval.iloc[:, 1],
    })
    print(result_table)

    plot_forecast_with_ci(train, test, predicted_mean, confidence_interval,
                           os.path.join(OUTPUT_DIR, "final_forecast_plot.png"))
    print(f"\nFinal forecast chart saved to {OUTPUT_DIR}/final_forecast_plot.png")