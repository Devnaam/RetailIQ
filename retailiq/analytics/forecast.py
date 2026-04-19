"""Revenue forecasting utilities."""

from __future__ import annotations

import pandas as pd


def forecast_next_month_revenue(df: pd.DataFrame, periods: int = 1) -> tuple[pd.DataFrame, str]:
    """Forecast monthly revenue with Prophet when available, otherwise use exponential smoothing."""

    monthly = (
        df.groupby(pd.Grouper(key="order_purchase_timestamp", freq="MS"))["revenue"]
        .sum()
        .reset_index()
        .rename(columns={"order_purchase_timestamp": "ds", "revenue": "y"})
        .sort_values("ds")
    )
    monthly = monthly[monthly["y"].notna()]
    if len(monthly) < 3:
        return pd.DataFrame(columns=["ds", "yhat", "yhat_lower", "yhat_upper"]), "Insufficient history"

    try:
        from prophet import Prophet

        model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
        model.fit(monthly)
        future = model.make_future_dataframe(periods=periods, freq="MS")
        forecast = model.predict(future)[["ds", "yhat", "yhat_lower", "yhat_upper"]]
        return forecast.tail(periods + min(24, len(monthly))), "Prophet"
    except Exception:
        forecast = monthly.copy()
        forecast["yhat"] = forecast["y"].ewm(span=4, adjust=False).mean()
        residual = (forecast["y"] - forecast["yhat"]).std() or forecast["y"].std() or 0
        next_month = forecast["ds"].max() + pd.offsets.MonthBegin(1)
        next_value = forecast["yhat"].iloc[-1]
        future = pd.DataFrame({"ds": [next_month], "yhat": [next_value], "yhat_lower": [next_value - 1.96 * residual], "yhat_upper": [next_value + 1.96 * residual]})
        history = forecast.rename(columns={"y": "actual"})[["ds", "yhat"]].tail(24)
        history["yhat_lower"] = history["yhat"] - 1.96 * residual
        history["yhat_upper"] = history["yhat"] + 1.96 * residual
        return pd.concat([history, future], ignore_index=True), "Exponential smoothing fallback"
