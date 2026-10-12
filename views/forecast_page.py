import plotly.graph_objects as go
import streamlit as st

from data_access import load_daily_revenue
from forecasting import (
    FORECAST_HORIZON,
    ROLLING_WINDOWS,
    TEST_SIZE,
    fit_and_forecast_with_ci,
    rolling_backtest,
    select_best_order,
    select_best_seasonal_order,
    split_train_test,
)
from formatting import format_money
from ui import ACCENT, FORECAST_BAND, POSITIVE, PRIMARY, card, chart_card, metric_card, page_header, style_chart

HISTORY_DAYS = 60

page_header(
    "Forecast",
    "Seasonal ARIMA forecast of daily revenue for the whole business (sidebar filters do not apply).",
)

try:
    daily = load_daily_revenue()
except FileNotFoundError as error:
    st.error(
        f"A required data file is missing ({error}). "
        "Run forecasting.py first."
    )
    st.stop()


@st.cache_data(show_spinner="Fitting forecasting models...")
def run_forecasts(series):
    arima_order, _ = select_best_order(series, d=0)
    (order, seasonal_order), _ = select_best_seasonal_order(series, d=0)

    train, test = split_train_test(series, test_size=TEST_SIZE)
    _, test_forecast, test_interval = fit_and_forecast_with_ci(
        train, order, steps=len(test), seasonal_order=seasonal_order)
    comparison = rolling_backtest(series, arima_order, (order, seasonal_order))

    _, future_forecast, future_interval = fit_and_forecast_with_ci(
        series, order, steps=FORECAST_HORIZON, seasonal_order=seasonal_order
    )
    label = f"SARIMA{order}x{seasonal_order}"
    return label, train, test, test_forecast, test_interval, comparison, future_forecast, future_interval


def forecast_figure(history, forecast, interval, actual=None):
    lower = interval.iloc[:, 0]
    upper = interval.iloc[:, 1]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(forecast.index) + list(forecast.index[::-1]),
        y=list(upper) + list(lower.iloc[::-1]),
        fill="toself", fillcolor=FORECAST_BAND, line={"width": 0},
        hoverinfo="skip", name="95% confidence interval",
    ))
    fig.add_trace(go.Scatter(
        x=history.index, y=history.values, name="Historical revenue",
        line={"color": PRIMARY},
    ))
    if actual is not None:
        fig.add_trace(go.Scatter(
            x=actual.index, y=actual.values, name="Actual",
            mode="lines+markers", line={"color": POSITIVE},
        ))
    fig.add_trace(go.Scatter(
        x=forecast.index, y=forecast.values, name="Forecast",
        line={"color": ACCENT, "dash": "dash"},
    ))
    fig.update_layout(yaxis_title="Revenue", hovermode="x unified")
    return style_chart(fig, money_axis="y", height=380)


(model_label, train, test, test_forecast, test_interval,
 comparison, future_forecast, future_interval) = run_forecasts(daily)

columns = st.columns(3)
metric_card(columns[0], "Model", model_label, help="Seasonal ARIMA with a weekly period, chosen by the lowest AIC")
metric_card(
    columns[1],
    f"Forecast, avg per day (next {FORECAST_HORIZON} days)",
    format_money(future_forecast.mean()),
)
metric_card(
    columns[2],
    f"Actual, avg per day (last {TEST_SIZE} days)",
    format_money(test.mean()),
)

chart_card(
    f"Next {FORECAST_HORIZON} days",
    forecast_figure(daily.iloc[-HISTORY_DAYS:], future_forecast, future_interval),
)
chart_card(
    f"Backtest: last {TEST_SIZE} days held out",
    forecast_figure(train.iloc[-HISTORY_DAYS:], test_forecast, test_interval, actual=test),
)

with card("Model comparison"):
    st.subheader(f"Model comparison: average over {ROLLING_WINDOWS} rolling {TEST_SIZE}-day windows")
    st.dataframe(
        comparison,
        hide_index=True,
        column_config={
            "MAE": st.column_config.NumberColumn(format="%.2f"),
            "RMSE": st.column_config.NumberColumn(format="%.2f"),
            "windows_won": st.column_config.NumberColumn("Windows won", format="%d"),
        },
    )