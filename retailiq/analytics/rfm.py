"""RFM segmentation using K-Means clustering."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


SEGMENT_LABELS = ["Lost", "At Risk", "Loyal", "Champions"]


def build_rfm_segments(df: pd.DataFrame, k: int = 4) -> pd.DataFrame:
    """Create RFM scores and cluster customers into four business segments."""

    if df.empty:
        return pd.DataFrame(columns=["customer_unique_id", "recency", "frequency", "monetary", "segment"])

    snapshot_date = df["order_purchase_timestamp"].max() + pd.Timedelta(days=1)
    rfm = (
        df.groupby("customer_unique_id")
        .agg(
            recency=("order_purchase_timestamp", lambda x: (snapshot_date - x.max()).days),
            frequency=("order_id", "nunique"),
            monetary=("revenue", "sum"),
        )
        .reset_index()
    )

    if len(rfm) < k:
        rfm["cluster"] = 0
        rfm["segment"] = "Champions"
        return rfm

    features = rfm[["recency", "frequency", "monetary"]].replace([np.inf, -np.inf], 0).fillna(0)
    scaled = StandardScaler().fit_transform(features)
    rfm["cluster"] = KMeans(n_clusters=k, n_init=20, random_state=42).fit_predict(scaled)

    cluster_scores = (
        rfm.groupby("cluster")
        .agg(recency=("recency", "mean"), frequency=("frequency", "mean"), monetary=("monetary", "mean"))
    )
    cluster_scores["score"] = (
        -cluster_scores["recency"].rank(method="first")
        + cluster_scores["frequency"].rank(method="first")
        + cluster_scores["monetary"].rank(method="first")
    )
    ordered_clusters = cluster_scores.sort_values("score").index.tolist()
    label_map = {cluster: SEGMENT_LABELS[i] for i, cluster in enumerate(ordered_clusters)}
    rfm["segment"] = rfm["cluster"].map(label_map)
    return rfm


def churn_probability_by_segment(rfm: pd.DataFrame) -> pd.DataFrame:
    """Estimate churn probability by segment from recency and frequency behavior."""

    if rfm.empty:
        return pd.DataFrame(columns=["segment", "churn_probability"])
    segment_stats = rfm.groupby("segment").agg(recency=("recency", "mean"), frequency=("frequency", "mean")).reset_index()
    recency_scaled = segment_stats["recency"] / segment_stats["recency"].max()
    frequency_scaled = 1 - (segment_stats["frequency"] / segment_stats["frequency"].max())
    segment_stats["churn_probability"] = ((recency_scaled * 0.7 + frequency_scaled * 0.3) * 100).clip(0, 100)
    return segment_stats[["segment", "churn_probability"]].sort_values("churn_probability", ascending=False)
