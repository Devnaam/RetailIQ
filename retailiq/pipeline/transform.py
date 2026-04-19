"""Feature engineering helpers for dashboard analytics."""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from retailiq.config import ALLOW_DEMO_DATA, BR_STATES, DATA_DIR, DATE_COLUMN
from retailiq.pipeline.ingest import build_star_schema, load_olist_csvs


def load_fact_orders(engine: Engine | None = None) -> tuple[pd.DataFrame, datetime | None, str]:
    """Load fact orders from PostgreSQL, CSVs, or generated demo data."""

    if engine is not None:
        try:
            fact = pd.read_sql("SELECT * FROM fact_orders", engine)
            freshness = get_latest_pipeline_run(engine)
            return prepare_fact_orders(fact), freshness, "PostgreSQL"
        except Exception:
            pass

    try:
        raw = load_olist_csvs(DATA_DIR)
        tables = build_star_schema(raw)
        return prepare_fact_orders(tables["fact_orders"]), None, "CSV"
    except Exception as exc:
        if ALLOW_DEMO_DATA:
            return prepare_fact_orders(generate_demo_fact_orders()), None, "Demo sample"
        raise RuntimeError(
            "Real Olist data was not found. Run `python -m retailiq.pipeline.download`, "
            "place the six CSV files in `data/`, or set RETAILIQ_DATA_DIR to their folder."
        ) from exc


def get_latest_pipeline_run(engine: Engine) -> datetime | None:
    """Return the latest successful or failed pipeline timestamp."""

    try:
        with engine.connect() as conn:
            value = conn.execute(text("SELECT MAX(run_at) FROM pipeline_runs")).scalar()
        return pd.to_datetime(value).to_pydatetime() if value else None
    except Exception:
        return None


def prepare_fact_orders(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize types and add reusable time features."""

    data = df.copy()
    date_columns = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for column in date_columns:
        if column in data.columns:
            data[column] = pd.to_datetime(data[column], errors="coerce")

    for column in ["price", "freight_value", "revenue", "review_score", "delivery_days"]:
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce")

    data["revenue"] = data.get("revenue", data.get("price", 0) + data.get("freight_value", 0)).fillna(0)
    data["product_category"] = data.get("product_category", "unknown").fillna("unknown")
    data["customer_state"] = data.get("customer_state", "NA").fillna("NA")
    data["month"] = data[DATE_COLUMN].dt.to_period("M").dt.to_timestamp()
    data["order_date"] = data[DATE_COLUMN].dt.date
    return data.dropna(subset=[DATE_COLUMN])


def apply_filters(
    df: pd.DataFrame,
    start_date: datetime,
    end_date: datetime,
    category: str,
    state: str,
) -> pd.DataFrame:
    """Filter the fact table by dashboard controls."""

    mask = (df[DATE_COLUMN].dt.date >= start_date.date()) & (df[DATE_COLUMN].dt.date <= end_date.date())
    filtered = df.loc[mask].copy()
    if category != "All":
        filtered = filtered[filtered["product_category"] == category]
    if state != "All":
        filtered = filtered[filtered["customer_state"] == state]
    return filtered


def monthly_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate monthly KPI values."""

    monthly = (
        df.groupby("month")
        .agg(
            revenue=("revenue", "sum"),
            total_orders=("order_id", "nunique"),
            customers=("customer_unique_id", "nunique"),
        )
        .reset_index()
        .sort_values("month")
    )
    monthly["aov"] = monthly["revenue"] / monthly["total_orders"].replace(0, np.nan)
    monthly["clv"] = monthly["revenue"] / monthly["customers"].replace(0, np.nan)
    return monthly.fillna(0)


def calculate_kpi_summary(df: pd.DataFrame) -> dict[str, dict[str, float]]:
    """Calculate current KPI values and month-over-month deltas."""

    monthly = monthly_kpis(df)
    total_revenue = float(df["revenue"].sum())
    total_orders = float(df["order_id"].nunique())
    customers = float(df["customer_unique_id"].nunique())
    values = {
        "Total Revenue": total_revenue,
        "Total Orders": total_orders,
        "Average Order Value": total_revenue / total_orders if total_orders else 0.0,
        "Customer Lifetime Value": total_revenue / customers if customers else 0.0,
    }
    metric_map = {
        "Total Revenue": "revenue",
        "Total Orders": "total_orders",
        "Average Order Value": "aov",
        "Customer Lifetime Value": "clv",
    }
    deltas: dict[str, float] = {}
    for label, column in metric_map.items():
        if len(monthly) >= 2:
            current = monthly[column].iloc[-1]
            previous = monthly[column].iloc[-2]
            deltas[label] = float(((current - previous) / previous) * 100) if previous else 0.0
        else:
            deltas[label] = 0.0
    return {label: {"value": values[label], "delta": deltas[label]} for label in values}


def generate_demo_fact_orders(rows: int = 6000) -> pd.DataFrame:
    """Generate realistic demo data when the Olist source is unavailable."""

    rng = np.random.default_rng(42)
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=730, freq="D")
    categories = [
        "health_beauty",
        "sports_leisure",
        "computers_accessories",
        "furniture_decor",
        "watches_gifts",
        "housewares",
        "auto",
        "toys",
    ]
    order_dates = rng.choice(dates, rows)
    prices = rng.gamma(shape=2.2, scale=65, size=rows).round(2)
    freight = rng.gamma(shape=1.4, scale=14, size=rows).round(2)
    delivered = pd.to_datetime(order_dates) + pd.to_timedelta(rng.integers(2, 24, rows), unit="D")
    statuses = rng.choice(["delivered", "shipped", "canceled", "processing", "invoiced"], rows, p=[0.86, 0.05, 0.03, 0.04, 0.02])

    return pd.DataFrame(
        {
            "order_id": [f"ord_{i:06d}" for i in range(rows)],
            "order_item_id": 1,
            "customer_id": [f"cust_{rng.integers(1, 3200):05d}" for _ in range(rows)],
            "customer_unique_id": [f"unique_{rng.integers(1, 2600):05d}" for _ in range(rows)],
            "product_id": [f"prod_{rng.integers(1, 900):04d}" for _ in range(rows)],
            "seller_id": [f"seller_{rng.integers(1, 180):04d}" for _ in range(rows)],
            "order_status": statuses,
            "customer_state": rng.choice(BR_STATES, rows),
            "seller_state": rng.choice(BR_STATES, rows),
            "product_category": rng.choice(categories, rows),
            "price": prices,
            "freight_value": freight,
            "revenue": prices + freight,
            "review_score": rng.choice([1, 2, 3, 4, 5], rows, p=[0.07, 0.08, 0.14, 0.31, 0.40]),
            "order_purchase_timestamp": pd.to_datetime(order_dates),
            "order_approved_at": pd.to_datetime(order_dates) + pd.to_timedelta(1, unit="D"),
            "order_delivered_carrier_date": pd.to_datetime(order_dates) + pd.to_timedelta(2, unit="D"),
            "order_delivered_customer_date": delivered,
            "order_estimated_delivery_date": pd.to_datetime(order_dates) + pd.to_timedelta(18, unit="D"),
            "delivery_days": (delivered - pd.to_datetime(order_dates)).days,
        }
    )
