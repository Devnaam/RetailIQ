"""Predictive analytics page."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from retailiq.analytics.churn import build_customer_features, train_churn_model
from retailiq.analytics.forecast import forecast_next_month_revenue
from retailiq.analytics.rfm import build_rfm_segments
from retailiq.ui.theme import format_figure


def render(df: pd.DataFrame) -> None:
    """Render forecasting and churn modeling."""

    st.title("Predictive Analytics")

    forecast, method = forecast_next_month_revenue(df)
    fig = go.Figure()
    if not forecast.empty:
        fig.add_trace(go.Scatter(x=forecast["ds"], y=forecast["yhat"], mode="lines+markers", name="forecast"))
        fig.add_trace(
            go.Scatter(
                x=list(forecast["ds"]) + list(forecast["ds"])[::-1],
                y=list(forecast["yhat_upper"]) + list(forecast["yhat_lower"])[::-1],
                fill="toself",
                fillcolor="rgba(0, 212, 255, 0.16)",
                line=dict(color="rgba(0,0,0,0)"),
                hoverinfo="skip",
                name="confidence interval",
            )
        )
    fig.update_layout(title=f"Next-Month Revenue Forecast ({method})")
    st.plotly_chart(format_figure(fig, 500), width="stretch")

    customer_features = build_customer_features(df)
    churn_result = train_churn_model(customer_features)
    metrics = churn_result["metrics"]
    predictions = churn_result["predictions"]
    drivers = churn_result["drivers"]

    col1, col2 = st.columns(2)
    col1.metric("Churn Model F1", f"{metrics['F1']:.2%}")
    col2.metric("AUC-ROC", f"{metrics['AUC-ROC']:.2%}")

    rfm = build_rfm_segments(df)
    segment_predictions = predictions.merge(rfm[["customer_unique_id", "segment"]], on="customer_unique_id", how="left")
    segment_summary = (
        segment_predictions.groupby("segment", as_index=False)["churn_probability"]
        .mean()
        .sort_values("churn_probability", ascending=False)
    )
    segment_summary["churn_probability"] *= 100
    left, right = st.columns(2)
    churn_fig = px.bar(segment_summary, x="segment", y="churn_probability", color="segment", title="Predicted Churn Probability by Segment")
    churn_fig.update_yaxes(ticksuffix="%")
    left.plotly_chart(format_figure(churn_fig), width="stretch")

    driver_fig = px.bar(drivers.sort_values("importance"), x="importance", y="feature", orientation="h", title="Top 5 Features Driving Churn")
    right.plotly_chart(format_figure(driver_fig), width="stretch")

    st.subheader("Customer Churn Scores")
    score_table = (
        segment_predictions[["customer_unique_id", "segment", "churn_probability"]]
        .assign(churn_probability=lambda data: (data["churn_probability"] * 100).round(1))
        .sort_values("churn_probability", ascending=False)
        .head(100)
    )
    st.dataframe(score_table, width="stretch", hide_index=True)
