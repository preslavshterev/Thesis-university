import plotly.graph_objects as go
import streamlit as st

from data_access import load_daily_revenue
from forecasting import (
    FORECAST_HORIZON,
    TEST_SIZE,
    compare_models_on_test,
    fit_and_forecast_with_ci,
    select_best_order,
    split_train_test,
)
from formatting import CURRENCY_SYMBOL, format_money

HISTORY_COLOR = "#2E6F9E"
ACTUAL_COLOR = "#2E8B57"
FORECAST_COLOR = "#E08A1E"
BAND_COLOR = "rgba(224, 138, 30, 0.2)"
HISTORY_DAYS = 60

st.title("Forecast")

try:
    daily = load_daily_revenue()
except FileNotFoundError as error:
    st.error(
        f"A required data file is missing ({error}). "
        "Run forecasting.py first."
    )
    st.stop()


@st.cache_data
def run_forecasts(series):
    order, _ = select_best_order(series, d=0)

    train, test = split_train_test(series, test_size=TEST_SIZE)
    _, test_forecast, test_interval = fit_and_forecast_with_ci(train, order, steps=len(test))
    comparison = compare_models_on_test(train, test, order)

    _, future_forecast, future_interval = fit_and_forecast_with_ci(
        series, order, steps=FORECAST_HORIZON
    )
    return order, train, test, test_forecast, test_interval, comparison, future_forecast, future_interval


def forecast_figure(history, forecast, interval, actual=None):
    lower = interval.iloc[:, 0]
    upper = interval.iloc[:, 1]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(forecast.index) + list(forecast.index[::-1]),
        y=list(upper) + list(lower.iloc[::-1]),
        fill="toself",
        fillcolor=BAND_COLOR,
        line={"width": 0},
        hoverinfo="skip",
        name="95% confidence interval",
    ))
    fig.add_trace(go.Scatter(
        x=history.index, y=history.values, name="Historical revenue",
        line={"color": HISTORY_COLOR},
    ))
    if actual is not None:
        fig.add_trace(go.Scatter(
            x=actual.index, y=actual.values, name="Actual",
            mode="lines+markers", line={"color": ACTUAL_COLOR},
        ))
    fig.add_trace(go.Scatter(
        x=forecast.index, y=forecast.values, name="Forecast",
        line={"color": FORECAST_COLOR, "dash": "dash"},
    ))
    fig.update_layout(
        yaxis_title="Revenue",
        yaxis_tickprefix=CURRENCY_SYMBOL,
        yaxis_tickformat=",",
        hovermode="x unified",
    )
    return fig


(order, train, test, test_forecast, test_interval,
 comparison, future_forecast, future_interval) = run_forecasts(daily)

st.info(
    "Daily revenue in this dataset shows no clear trend or seasonality, "
    "so the best model forecasts roughly the average level with a wide interval."
)

col1, col2, col3 = st.columns(3)
col1.metric("Model", f"ARIMA{order}", help="Order chosen by the lowest AIC")
col2.metric(f"Forecast, avg per day (next {FORECAST_HORIZON} days)", format_money(future_forecast.mean()))
col3.metric(f"Actual, avg per day (last {TEST_SIZE} days)", format_money(test.mean()))

st.subheader(f"Next {FORECAST_HORIZON} days")
st.plotly_chart(forecast_figure(daily.iloc[-HISTORY_DAYS:], future_forecast, future_interval))

st.subheader(f"Backtest: last {TEST_SIZE} days held out")
st.plotly_chart(
    forecast_figure(train.iloc[-HISTORY_DAYS:], test_forecast, test_interval, actual=test)
)

st.subheader("Model comparison on the held-out days")
st.dataframe(
    comparison,
    hide_index=True,
    column_config={
        "MAE": st.column_config.NumberColumn(format="%.2f"),
        "RMSE": st.column_config.NumberColumn(format="%.2f"),
    },
)