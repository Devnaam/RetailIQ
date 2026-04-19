"""Executive KPI dashboard page."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from retailiq.pipeline.transform import calculate_kpi_summary, monthly_kpis
from retailiq.ui.theme import format_figure


STATE_CENTROIDS = {
    "AC": (-8.77, -70.55),
    "AL": (-9.71, -35.73),
    "AM": (-3.07, -61.66),
    "AP": (1.41, -51.77),
    "BA": (-12.96, -38.51),
    "CE": (-3.71, -38.54),
    "DF": (-15.83, -47.86),
    "ES": (-19.19, -40.34),
    "GO": (-16.64, -49.31),
    "MA": (-2.55, -44.30),
    "MG": (-18.10, -44.38),
    "MS": (-20.51, -54.54),
    "MT": (-12.64, -55.42),
    "PA": (-5.53, -52.29),
    "PB": (-7.06, -35.55),
    "PE": (-8.28, -35.07),
    "PI": (-8.28, -43.68),
    "PR": (-24.89, -51.55),
    "RJ": (-22.84, -43.15),
    "RN": (-5.22, -36.52),
    "RO": (-11.22, -62.80),
    "RR": (1.89, -61.22),
    "RS": (-30.01, -51.22),
    "SC": (-27.33, -49.44),
    "SE": (-10.90, -37.07),
    "SP": (-23.55, -46.64),
    "TO": (-10.25, -48.25),
}


def render(df: pd.DataFrame) -> None:
    """Render the executive dashboard."""

    st.title("RetailIQ - Executive Overview")
    kpis = calculate_kpi_summary(df)
    monthly = monthly_kpis(df).tail(24)

    cols = st.columns(4)
    for column, (label, payload) in zip(cols, kpis.items()):
        value = payload["value"]
        display = f"R$ {value:,.0f}" if label != "Total Orders" else f"{value:,.0f}"
        column.metric(label, display, f"{payload['delta']:+.1f}% MoM")

    trend = px.line(monthly, x="month", y="revenue", markers=True, title="Revenue Trend - Last 24 Months")
    trend.update_traces(line=dict(width=3))
    st.plotly_chart(format_figure(trend), width="stretch")

    left, right = st.columns(2)
    category_revenue = (
        df.groupby("product_category", as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)
        .head(10)
        .sort_values("revenue")
    )
    bar = px.bar(category_revenue, x="revenue", y="product_category", orientation="h", title="Top 10 Product Categories by Revenue")
    left.plotly_chart(format_figure(bar), width="stretch")

    status = df.groupby("order_status", as_index=False)["order_id"].nunique().sort_values("order_id", ascending=False)
    funnel = go.Figure(go.Funnel(y=status["order_status"], x=status["order_id"], marker={"color": px.colors.qualitative.Set2}))
    funnel.update_layout(title="Order Status Distribution")
    right.plotly_chart(format_figure(funnel), width="stretch")

    geo = df.groupby("customer_state", as_index=False)["revenue"].sum()
    geo["lat"] = geo["customer_state"].map(lambda state: STATE_CENTROIDS.get(state, (None, None))[0])
    geo["lon"] = geo["customer_state"].map(lambda state: STATE_CENTROIDS.get(state, (None, None))[1])
    geo = geo.dropna(subset=["lat", "lon"])
    map_fig = px.scatter_geo(
        geo,
        lat="lat",
        lon="lon",
        size="revenue",
        color="revenue",
        hover_name="customer_state",
        scope="south america",
        title="Geographic Revenue Heatmap by Brazilian State",
        color_continuous_scale="Turbo",
    )
    map_fig.update_geos(bgcolor="rgba(0,0,0,0)", landcolor="#182333", lakecolor="#070b11")
    st.plotly_chart(format_figure(map_fig, 500), width="stretch")
