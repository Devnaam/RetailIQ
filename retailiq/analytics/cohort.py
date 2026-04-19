"""Cohort retention analysis."""

from __future__ import annotations

import pandas as pd


def cohort_retention_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Build a monthly customer cohort retention matrix."""

    if df.empty:
        return pd.DataFrame()

    data = df[["customer_unique_id", "order_purchase_timestamp"]].dropna().copy()
    data["order_month"] = data["order_purchase_timestamp"].dt.to_period("M")
    data["cohort_month"] = data.groupby("customer_unique_id")["order_month"].transform("min")
    data["period_number"] = (data["order_month"] - data["cohort_month"]).apply(lambda period: period.n)

    cohorts = data.groupby(["cohort_month", "period_number"])["customer_unique_id"].nunique().reset_index()
    matrix = cohorts.pivot(index="cohort_month", columns="period_number", values="customer_unique_id")
    cohort_sizes = matrix.iloc[:, 0]
    retention = matrix.divide(cohort_sizes, axis=0).fillna(0) * 100
    retention.index = retention.index.astype(str)
    return retention.round(1)
