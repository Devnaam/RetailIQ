"""Customer analytics page."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from retailiq.analytics.cohort import cohort_retention_matrix
from retailiq.analytics.rfm import build_rfm_segments, churn_probability_by_segment
from retailiq.ui.theme import format_figure


def render(df: pd.DataFrame) -> pd.DataFrame:
    """Render customer analytics and return the RFM table for other pages."""

    st.title("Customer Analytics")
    rfm = build_rfm_segments(df)
    churn = churn_probability_by_segment(rfm)

    left, right = st.columns([2, 1])
    scatter = px.scatter_3d(
        rfm,
        x="recency",
        y="frequency",
        z="monetary",
        color="segment",
        hover_name="customer_unique_id",
        title="RFM Customer Segments",
    )
    left.plotly_chart(format_figure(scatter, 520), width="stretch")

    churn_fig = px.bar(churn, x="segment", y="churn_probability", color="segment", title="Churn Probability by Segment")
    churn_fig.update_yaxes(ticksuffix="%")
    right.plotly_chart(format_figure(churn_fig, 520), width="stretch")

    retention = cohort_retention_matrix(df)
    heatmap = px.imshow(
        retention,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="Viridis",
        title="Monthly Cohort Retention (%)",
    )
    st.plotly_chart(format_figure(heatmap, 520), width="stretch")

    st.subheader("Top 10 Customers by Lifetime Value")
    top_customers = (
        rfm.sort_values("monetary", ascending=False)
        .head(10)[["customer_unique_id", "segment", "recency", "frequency", "monetary"]]
        .rename(columns={"monetary": "lifetime_value_brl"})
    )
    st.dataframe(top_customers, width="stretch", hide_index=True)
    return rfm
