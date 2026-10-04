import os

import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

DAILY_SERIES_PATH = "output/daily_revenue_series.csv"
OUTPUT_DIR = "output"
TEST_SIZE = 14

ARIMA_ORDER = (0, 0, 0)


# =====================================================================
# 1. Load the prepared series
# =====================================================================

def load_daily_series(path):
    series = pd.read_csv(path, index_col=0, parse_dates=True)["revenue"]
    series = series.asfreq("D")
    return series


# =====================================================================
# 2. Train / test split
# =====================================================================

def split_train_test(series, test_size=TEST_SIZE):
    """Hold out the last `test_size` days as the test set; everything
    before that is the train set. This is a chronological split (not a
    random shuffle, which is what train/test splitting usually means
    for other kinds of data) -- shuffling would be meaningless here,
    since forecasting is specifically about predicting what comes
    *after* the data the model has seen."""
    train = series.iloc[:-test_size]
    test = series.iloc[-test_size:]
    return train, test


# =====================================================================
# 3. Train on the train set, forecast the test period
# =====================================================================

def fit_and_forecast(train, order, steps):
    """Fit ARIMA using only the train portion, then forecast exactly
    `steps` days ahead. Because `train` carries a daily frequency
    (set by asfreq("D") when it was loaded), statsmodels automatically
    labels the forecasted values with the correct following dates --
    there is no need to build the future date range by hand, unlike
    the moving-average forecast in Day 23."""
    model = ARIMA(train, order=order)
    fitted_model = model.fit()
    forecast = fitted_model.forecast(steps=steps)
    return fitted_model, forecast


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    daily = load_daily_series(DAILY_SERIES_PATH)

    train, test = split_train_test(daily, test_size=TEST_SIZE)
    print(f"Train set: {len(train)} days, from {train.index.min().date()} to {train.index.max().date()}")
    print(f"Test set:  {len(test)} days, from {test.index.min().date()} to {test.index.max().date()}")

    print(f"\n=== TRAINING ARIMA{ARIMA_ORDER} ON THE TRAIN SET ===")
    fitted_model, forecast = fit_and_forecast(train, ARIMA_ORDER, steps=TEST_SIZE)

    comparison = pd.DataFrame({
        "actual": test,
        "forecast": forecast,
    })
    print("\n=== ACTUAL vs FORECAST (test period) ===")
    print(comparison)

    comparison.to_csv(os.path.join(OUTPUT_DIR, "arima_test_forecast.csv"))
    print(f"\nSaved actual-vs-forecast table to {OUTPUT_DIR}/arima_test_forecast.csv")