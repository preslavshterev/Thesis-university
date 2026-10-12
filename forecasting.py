import os
import warnings

import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tools.sm_exceptions import ConvergenceWarning
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import SimpleExpSmoothing
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller

FACT_SALES_PATH = "output/fact_sales.parquet"
DAILY_SERIES_PATH = "output/daily_revenue_series.csv"
OUTPUT_DIR = "output"

TEST_SIZE = 14
FORECAST_HORIZON = 14
SEASONAL_PERIOD = 7
ROLLING_WINDOWS = 8


def build_daily_series(completed):
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

    monthly = completed.set_index("order_date")["line_total"].resample("MS").sum()
    return monthly


def load_daily_series(path=DAILY_SERIES_PATH):
    series = pd.read_csv(path, index_col=0, parse_dates=True, float_precision="round_trip")["revenue"]
    series = series.asfreq("D")
    return series


def decompose_daily_series(daily_series, period=7):
    decomposition = seasonal_decompose(daily_series, model="additive", period=period)
    return decomposition


def plot_decomposition(decomposition, output_path):
    fig = decomposition.plot()
    fig.set_size_inches(12, 8)

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def moving_average_forecast(series, window=7, horizon=FORECAST_HORIZON):
    last_average = series.rolling(window=window).mean().iloc[-1]

    future_dates = pd.date_range(
        start=series.index[-1] + pd.Timedelta(days=1), periods=horizon, freq="D"
    )
    forecast = pd.Series(last_average, index=future_dates)
    return forecast


def exponential_smoothing_forecast(series, horizon=FORECAST_HORIZON):
    model = SimpleExpSmoothing(series, initialization_method="estimated")
    fitted_model = model.fit()
    forecast = fitted_model.forecast(horizon)
    return fitted_model, forecast


def plot_baseline_forecasts(series, ma_forecast, es_forecast, output_path, last_n_days=90):
    recent_history = series.iloc[-last_n_days:]

    plt.figure(figsize=(12, 6))
    plt.plot(recent_history.index, recent_history.values, label="Historical revenue")
    plt.plot(ma_forecast.index, ma_forecast.values, label="Moving average forecast", linestyle="--")
    plt.plot(es_forecast.index, es_forecast.values, label="Exponential smoothing forecast", linestyle="--")

    plt.title(f"Baseline forecasts -- last {last_n_days} days + {len(ma_forecast)}-day forecast")
    plt.ylabel("Revenue")
    plt.legend()

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def check_stationarity(series, label="series"):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        result = adfuller(series.dropna())
    test_statistic, p_value = result[0], result[1]

    is_stationary = p_value < 0.05
    print(f"ADF test on {label}: statistic={test_statistic:.4f}, p-value={p_value:.4f} "
          f"-> {'stationary' if is_stationary else 'NOT stationary'}")

    return is_stationary


def plot_acf_pacf(series, output_path, lags=30):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    plot_acf(series.dropna(), lags=lags, ax=axes[0])
    plot_pacf(series.dropna(), lags=lags, ax=axes[1])

    axes[0].set_title("Autocorrelation (ACF)")
    axes[1].set_title("Partial autocorrelation (PACF)")

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def select_best_order(series, d, p_range=range(0, 3), q_range=range(0, 3)):
    best_aic = float("inf")
    best_order = None

    for p in p_range:
        for q in q_range:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    model = ARIMA(series, order=(p, d, q))
                    fitted = model.fit()
                print(f"ARIMA({p},{d},{q}) -> AIC={fitted.aic:.2f}")

                if fitted.aic < best_aic:
                    best_aic = fitted.aic
                    best_order = (p, d, q)
            except Exception as error:
                print(f"ARIMA({p},{d},{q}) -> failed to fit ({error})")

    return best_order, best_aic


def select_best_seasonal_order(series, d, period=SEASONAL_PERIOD,
                               p_range=range(0, 3), q_range=range(0, 2),
                               P_range=range(0, 2), Q_range=range(0, 2)):
    best_aic = float("inf")
    best_model = None

    for p in p_range:
        for q in q_range:
            for P in P_range:
                for Q in Q_range:
                    order = (p, d, q)
                    seasonal_order = (P, 0, Q, period)
                    try:
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore")
                            fitted = ARIMA(series, order=order, seasonal_order=seasonal_order).fit()
                        print(f"SARIMA{order}x{seasonal_order} -> AIC={fitted.aic:.2f}")

                        if fitted.aic < best_aic:
                            best_aic = fitted.aic
                            best_model = (order, seasonal_order)
                    except Exception as error:
                        print(f"SARIMA{order}x{seasonal_order} -> failed to fit ({error})")

    return best_model, best_aic


def fit_arima(series, order, seasonal_order=(0, 0, 0, 0)):
    model = ARIMA(series, order=order, seasonal_order=seasonal_order)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        fitted_model = model.fit()

    return fitted_model


def split_train_test(series, test_size=TEST_SIZE):
    train = series.iloc[:-test_size]
    test = series.iloc[-test_size:]
    return train, test


def fit_and_forecast_with_ci(train, order, steps, alpha=0.05, seasonal_order=(0, 0, 0, 0)):
    fitted_model = fit_arima(train, order, seasonal_order)

    forecast_result = fitted_model.get_forecast(steps=steps)
    predicted_mean = forecast_result.predicted_mean
    confidence_interval = forecast_result.conf_int(alpha=alpha)

    return fitted_model, predicted_mean, confidence_interval


def calculate_mae(actual, forecast):
    return (actual - forecast).abs().mean()


def calculate_rmse(actual, forecast):
    return ((actual - forecast) ** 2).mean() ** 0.5


def calculate_mape(actual, forecast):
    non_zero_mask = actual != 0
    excluded_days = (~non_zero_mask).sum()

    percentage_errors = (actual[non_zero_mask] - forecast[non_zero_mask]).abs() / actual[non_zero_mask]
    mape = percentage_errors.mean() * 100

    return mape, excluded_days


def seasonal_profile_forecast(series, horizon=FORECAST_HORIZON, weeks=4):
    recent = series.iloc[-7 * weeks:]
    profile = recent.groupby(recent.index.dayofweek).mean()

    future_dates = pd.date_range(
        start=series.index[-1] + pd.Timedelta(days=1), periods=horizon, freq="D"
    )
    return pd.Series(profile.loc[future_dates.dayofweek].values, index=future_dates)


def compare_models_on_test(train, test, arima_order, seasonal_model=None):
    horizon = len(test)

    ma_forecast = moving_average_forecast(train, window=7, horizon=horizon)
    _, es_forecast = exponential_smoothing_forecast(train, horizon=horizon)
    profile_forecast = seasonal_profile_forecast(train, horizon=horizon)
    arima_forecast = fit_arima(train, arima_order).forecast(steps=horizon)

    forecasts = {
        "Moving average (7 days)": ma_forecast,
        "Exponential smoothing": es_forecast,
        "Weekday profile (4 weeks)": profile_forecast,
        f"ARIMA{arima_order}": arima_forecast,
    }

    if seasonal_model is not None:
        order, seasonal_order = seasonal_model
        forecasts[f"SARIMA{order}x{seasonal_order}"] = fit_arima(
            train, order, seasonal_order).forecast(steps=horizon)

    rows = []
    for model_name, forecast in forecasts.items():
        aligned = pd.Series(forecast.values, index=test.index)
        rows.append({
            "model": model_name,
            "MAE": calculate_mae(test, aligned),
            "RMSE": calculate_rmse(test, aligned),
        })

    return pd.DataFrame(rows)


def rolling_backtest(series, arima_order, seasonal_model, n_windows=ROLLING_WINDOWS, horizon=TEST_SIZE):
    results = []

    for window in range(n_windows, 0, -1):
        end = len(series) - (window - 1) * horizon
        train = series.iloc[:end - horizon]
        test = series.iloc[end - horizon:end]

        comparison = compare_models_on_test(train, test, arima_order, seasonal_model)
        comparison["window"] = n_windows - window
        results.append(comparison)

    all_results = pd.concat(results)
    all_results["won"] = all_results["MAE"] == all_results.groupby("window")["MAE"].transform("min")

    summary = all_results.groupby("model", sort=False).agg(
        MAE=("MAE", "mean"),
        RMSE=("RMSE", "mean"),
        windows_won=("won", "sum"),
    ).reset_index()
    return summary


def plot_daily_errors(comparison, output_path):
    absolute_error = (comparison["actual"] - comparison["forecast"]).abs()

    plt.figure(figsize=(12, 5))
    plt.bar(absolute_error.index.strftime("%Y-%m-%d"), absolute_error.values)
    plt.xticks(rotation=45, ha="right")

    plt.title("Absolute forecast error per day (test period)")
    plt.ylabel("Absolute error")

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


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

    fact_sales = pd.read_parquet(FACT_SALES_PATH)
    completed = fact_sales[fact_sales["status"] == "completed"]

    print("=== STEP 1: BUILDING TIME SERIES ===")

    daily = build_daily_series(completed)
    weekly = build_weekly_series(completed)
    monthly = build_monthly_series(completed)
    print(f"Daily series:   {len(daily)} days, from {daily.index.min().date()} to {daily.index.max().date()}")
    print(f"Weekly series:  {len(weekly)} weeks")
    print(f"Monthly series: {len(monthly)} months")

    daily.to_csv(os.path.join(OUTPUT_DIR, "daily_revenue_series.csv"), header=["revenue"])
    weekly.to_csv(os.path.join(OUTPUT_DIR, "weekly_revenue_series.csv"), header=["revenue"])
    monthly.to_csv(os.path.join(OUTPUT_DIR, "monthly_revenue_series.csv"), header=["revenue"])

    print("\n=== STEP 2: DECOMPOSITION (trend / weekly seasonality / noise) ===")

    decomposition = decompose_daily_series(daily, period=7)
    plot_decomposition(decomposition, os.path.join(OUTPUT_DIR, "daily_decomposition.png"))
    print(f"Saved {OUTPUT_DIR}/daily_decomposition.png")

    print(f"\n=== STEP 3: BASELINE FORECASTS (next {FORECAST_HORIZON} days) ===")

    ma_forecast = moving_average_forecast(daily, window=7, horizon=FORECAST_HORIZON)
    fitted_ses, es_forecast = exponential_smoothing_forecast(daily, horizon=FORECAST_HORIZON)
    print(f"Moving average forecast (flat):       {ma_forecast.iloc[0]:.2f}")
    print(f"Exponential smoothing forecast (flat): {es_forecast.iloc[0]:.2f} "
          f"(alpha = {fitted_ses.params['smoothing_level']:.4f})")
    plot_baseline_forecasts(daily, ma_forecast, es_forecast, os.path.join(OUTPUT_DIR, "baseline_forecasts.png"))

    print("\n=== STEP 4: ARIMA -- STATIONARITY AND ORDER SELECTION ===")

    is_stationary = check_stationarity(daily, label="original daily series")
    d = 0 if is_stationary else 1
    if is_stationary:
        differenced = daily
    else:
        differenced = daily.diff().dropna()
        check_stationarity(differenced, label="differenced series (d=1)")
    print(f"Chosen d (differencing order) = {d}")

    plot_acf_pacf(differenced, os.path.join(OUTPUT_DIR, "acf_pacf.png"))

    best_order, best_aic = select_best_order(daily, d=d)
    print(f"Best order found: ARIMA{best_order} with AIC={best_aic:.2f}")

    print("\n=== STEP 4B: SEASONAL ARIMA (weekly period = 7) ===")

    seasonal_model, seasonal_aic = select_best_seasonal_order(daily, d=d)
    seasonal_label = f"SARIMA{seasonal_model[0]}x{seasonal_model[1]}"
    print(f"Best seasonal model: {seasonal_label} with AIC={seasonal_aic:.2f}")

    print("\n=== STEP 5: TRAIN/TEST SPLIT AND FORECAST ===")

    train, test = split_train_test(daily, test_size=TEST_SIZE)
    print(f"Train set: {len(train)} days, from {train.index.min().date()} to {train.index.max().date()}")
    print(f"Test set:  {len(test)} days, from {test.index.min().date()} to {test.index.max().date()}")

    fitted_model, predicted_mean, confidence_interval = fit_and_forecast_with_ci(
        train, seasonal_model[0], steps=TEST_SIZE, seasonal_order=seasonal_model[1]
    )

    comparison = pd.DataFrame({"actual": test, "forecast": predicted_mean})
    comparison.to_csv(os.path.join(OUTPUT_DIR, "arima_test_forecast.csv"))
    print(comparison)

    print(f"\n=== STEP 6: ACCURACY METRICS ({seasonal_label}, test period) ===")

    mae = calculate_mae(comparison["actual"], comparison["forecast"])
    rmse = calculate_rmse(comparison["actual"], comparison["forecast"])
    mape, excluded_days = calculate_mape(comparison["actual"], comparison["forecast"])
    print(f"MAE:  {mae:.2f}")
    print(f"RMSE: {rmse:.2f}")
    print(f"MAPE: {mape:.2f}% (excluded {excluded_days} day(s) with actual = 0)")
    print(f"MAE as a percentage of the mean actual value: {(mae / comparison['actual'].mean()) * 100:.1f}%")

    plot_daily_errors(comparison, os.path.join(OUTPUT_DIR, "forecast_errors.png"))

    print("\n=== STEP 7: ALL MODELS ON THE SAME TEST DAYS ===")

    model_comparison = compare_models_on_test(train, test, best_order, seasonal_model)
    print(model_comparison.to_string(index=False, float_format=lambda value: f"{value:.2f}"))

    print(f"\n=== STEP 7B: ROLLING BACKTEST ({ROLLING_WINDOWS} windows of {TEST_SIZE} days) ===\n")
    rolling = rolling_backtest(daily, best_order, seasonal_model)
    print(rolling.to_string(index=False, float_format=lambda value: f"{value:.2f}"))

    plot_forecast_with_ci(train, test, predicted_mean, confidence_interval,
                           os.path.join(OUTPUT_DIR, "final_forecast_plot.png"))
    print(f"\nFinal forecast chart saved to {OUTPUT_DIR}/final_forecast_plot.png")