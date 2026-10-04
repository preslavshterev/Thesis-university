import os

import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.tsa.holtwinters import SimpleExpSmoothing

DAILY_SERIES_PATH = "output/daily_revenue_series.csv"
OUTPUT_DIR = "output"
FORECAST_HORIZON = 14


# =====================================================================
# 1. Load the prepared series
# =====================================================================

def load_daily_series(path):
    series = pd.read_csv(path, index_col=0, parse_dates=True)["revenue"]
    series = series.asfreq("D")
    return series


# =====================================================================
# 2. Moving average forecast
# =====================================================================

def moving_average_forecast(series, window=7, horizon=FORECAST_HORIZON):
    last_average = series.rolling(window=window).mean().iloc[-1]

    future_dates = pd.date_range(
        start=series.index[-1] + pd.Timedelta(days=1), periods=horizon, freq="D"
    )
    forecast = pd.Series(last_average, index=future_dates)
    return forecast


# =====================================================================
# 3. Simple exponential smoothing forecast
# =====================================================================

def exponential_smoothing_forecast(series, horizon=FORECAST_HORIZON):
    model = SimpleExpSmoothing(series, initialization_method="estimated")
    fitted_model = model.fit()
    forecast = fitted_model.forecast(horizon)
    return fitted_model, forecast


# =====================================================================
# 4. Plot
# =====================================================================

def plot_baseline_forecasts(series, ma_forecast, es_forecast, output_path, last_n_days=90):
    recent_history = series.iloc[-last_n_days:]

    plt.figure(figsize=(12, 6))
    plt.plot(recent_history.index, recent_history.values, label="Historical revenue")
    plt.plot(ma_forecast.index, ma_forecast.values, label="Moving average forecast", linestyle="--")
    plt.plot(es_forecast.index, es_forecast.values, label="Exponential smoothing forecast", linestyle="--")
    plt.title(f"Baseline forecasts -- last {last_n_days} days + {FORECAST_HORIZON}-day forecast")
    plt.ylabel("Revenue")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    daily = load_daily_series(DAILY_SERIES_PATH)

    print(f"=== MOVING AVERAGE FORECAST (window=7, horizon={FORECAST_HORIZON} days) ===")
    ma_forecast = moving_average_forecast(daily, window=7, horizon=FORECAST_HORIZON)
    print(ma_forecast)

    print(f"\n=== EXPONENTIAL SMOOTHING FORECAST (horizon={FORECAST_HORIZON} days) ===")
    fitted_model, es_forecast = exponential_smoothing_forecast(daily, horizon=FORECAST_HORIZON)
    print(f"Fitted smoothing level (alpha): {fitted_model.params['smoothing_level']:.4f}")
    print(es_forecast)

    plot_baseline_forecasts(daily, ma_forecast, es_forecast, os.path.join(OUTPUT_DIR, "baseline_forecasts.png"))
    print(f"\nComparison chart saved to {OUTPUT_DIR}/baseline_forecasts.png")