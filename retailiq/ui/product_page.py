"""Product and seller intelligence page."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from retailiq.ui.theme import format_figure


def render(df: pd.DataFrame) -> None:
    """Render product and seller intelligence."""

    st.title("Product & Seller Intelligence")

    product_perf = (
        df.groupby(["product_id", "product_category"], as_index=False)
        .agg(revenue=("revenue", "sum"), review_score=("review_score", "mean"), orders=("order_id", "nunique"))
        .dropna(subset=["product_id"])
    )
    matrix = px.scatter(
        product_perf,
        x="revenue",
        y="review_score",
        size="orders",
        color="product_category",
        hover_name="product_id",
        title="Product Performance Matrix",
    )
    st.plotly_chart(format_figure(matrix, 520), width="stretch")

    left, right = st.columns(2)
    sellers = (
        df.groupby("seller_id", as_index=False)
        .agg(revenue=("revenue", "sum"), rating=("review_score", "mean"), delivery_time=("delivery_days", "mean"), orders=("order_id", "nunique"))
        .dropna(subset=["seller_id"])
        .sort_values("revenue", ascending=False)
        .head(15)
    )
    sellers = sellers.rename(columns={"delivery_time": "avg_delivery_days", "rating": "avg_rating"})
    left.subheader("Seller Performance Leaderboard")
    left.dataframe(sellers, width="stretch", hide_index=True)

    sentiment = df.assign(
        sentiment=pd.cut(
            df["review_score"],
            bins=[0, 2, 3, 5],
            labels=["negative", "neutral", "positive"],
            include_lowest=True,
        )
    )
    sentiment_counts = sentiment.groupby("sentiment", observed=False)["order_id"].nunique().reset_index()
    sentiment_fig = px.pie(sentiment_counts, names="sentiment", values="order_id", title="Review Sentiment Distribution", hole=0.45)
    right.plotly_chart(format_figure(sentiment_fig), width="stretch")

    box = px.box(df.dropna(subset=["delivery_days"]), x="customer_state", y="delivery_days", color="customer_state", title="Delivery Time Analysis by Region")
    st.plotly_chart(format_figure(box, 520), width="stretch")

    monthly_product_orders = (
        df.groupby(["product_id", "product_category", "month"], as_index=False)["order_id"]
        .nunique()
        .rename(columns={"order_id": "orders"})
    )
    slow_movers = (
        monthly_product_orders.groupby(["product_id", "product_category"], as_index=False)["orders"]
        .mean()
        .query("orders < 5")
        .sort_values("orders")
        .head(50)
    )
    st.subheader("Slow-Moving Inventory")
    st.dataframe(slow_movers, width="stretch", hide_index=True)
