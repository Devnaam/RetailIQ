"""CSV to PostgreSQL ingestion for the Olist dataset."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from retailiq.config import DATABASE_URL, DATA_DIR
from retailiq.pipeline.models import Base


REQUIRED_FILES = {
    "orders": "olist_orders_dataset.csv",
    "items": "olist_order_items_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
}


@dataclass(frozen=True)
class IngestResult:
    """Summary of an ingestion run."""

    status: str
    message: str
    rows_loaded: int
    run_at: datetime


def get_engine(database_url: str = DATABASE_URL) -> Engine:
    """Create a SQLAlchemy engine."""

    return create_engine(database_url, pool_pre_ping=True)


def _read_csv(data_dir: Path, file_name: str) -> pd.DataFrame:
    path = data_dir / file_name
    if not path.exists():
        raise FileNotFoundError(f"Missing required CSV: {path}")
    return pd.read_csv(path)


def load_olist_csvs(data_dir: Path = DATA_DIR) -> dict[str, pd.DataFrame]:
    """Load all required Olist CSVs from disk."""

    return {name: _read_csv(data_dir, file_name) for name, file_name in REQUIRED_FILES.items()}


def _clean_dates(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce")
    return df


def build_star_schema(raw: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Transform raw Olist tables into fact and dimension tables."""

    orders = _clean_dates(
        raw["orders"].copy(),
        [
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    )
    items = raw["items"].copy()
    customers = raw["customers"].copy()
    products = raw["products"].copy()
    sellers = raw["sellers"].copy()
    reviews = raw["reviews"].copy()

    products["product_category_name"] = products["product_category_name"].fillna("unknown")
    reviews_agg = reviews.groupby("order_id", as_index=False)["review_score"].mean()

    fact = (
        orders.merge(items, on="order_id", how="left")
        .merge(customers, on="customer_id", how="left")
        .merge(products, on="product_id", how="left")
        .merge(sellers, on="seller_id", how="left", suffixes=("_customer", "_seller"))
        .merge(reviews_agg, on="order_id", how="left")
    )

    fact["price"] = pd.to_numeric(fact["price"], errors="coerce").fillna(0.0)
    fact["freight_value"] = pd.to_numeric(fact["freight_value"], errors="coerce").fillna(0.0)
    fact["revenue"] = fact["price"] + fact["freight_value"]
    fact["product_category"] = fact["product_category_name"].fillna("unknown")
    fact["delivery_days"] = (
        fact["order_delivered_customer_date"] - fact["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400

    fact_orders = fact[
        [
            "order_id",
            "order_item_id",
            "customer_id",
            "customer_unique_id",
            "product_id",
            "seller_id",
            "order_status",
            "customer_state",
            "seller_state",
            "product_category",
            "price",
            "freight_value",
            "revenue",
            "review_score",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
            "delivery_days",
        ]
    ].copy()

    dim_customers = customers.rename(
        columns={
            "customer_zip_code_prefix": "zip_code_prefix",
            "customer_city": "city",
            "customer_state": "state",
        }
    )[["customer_id", "customer_unique_id", "zip_code_prefix", "city", "state"]]

    dim_products = products.rename(
        columns={
            "product_category_name": "category",
            "product_name_lenght": "name_length",
            "product_description_lenght": "description_length",
            "product_photos_qty": "photos_qty",
            "product_weight_g": "weight_g",
            "product_length_cm": "length_cm",
            "product_height_cm": "height_cm",
            "product_width_cm": "width_cm",
        }
    )[
        [
            "product_id",
            "category",
            "name_length",
            "description_length",
            "photos_qty",
            "weight_g",
            "length_cm",
            "height_cm",
            "width_cm",
        ]
    ]

    dim_sellers = sellers.rename(
        columns={
            "seller_zip_code_prefix": "zip_code_prefix",
            "seller_city": "city",
            "seller_state": "state",
        }
    )[["seller_id", "zip_code_prefix", "city", "state"]]

    return {
        "fact_orders": fact_orders,
        "dim_customers": dim_customers,
        "dim_products": dim_products,
        "dim_sellers": dim_sellers,
    }


def write_schema_to_database(tables: dict[str, pd.DataFrame], engine: Engine) -> int:
    """Create tables and write transformed data to PostgreSQL."""

    Base.metadata.create_all(engine)
    loaded = 0
    for table_name, df in tables.items():
        df.to_sql(table_name, engine, if_exists="replace", index=False, chunksize=5000, method="multi")
        loaded += len(df)
    return loaded


def record_pipeline_run(engine: Engine, status: str, message: str) -> None:
    """Persist the latest pipeline run metadata."""

    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO pipeline_runs (run_at, status, message) VALUES (:run_at, :status, :message)"),
            {"run_at": datetime.utcnow(), "status": status, "message": message},
        )


def run_pipeline(data_dir: Path = DATA_DIR, database_url: str = DATABASE_URL) -> IngestResult:
    """Run the full CSV to PostgreSQL ingestion pipeline."""

    run_at = datetime.utcnow()
    engine = get_engine(database_url)
    try:
        raw = load_olist_csvs(data_dir)
        tables = build_star_schema(raw)
        rows_loaded = write_schema_to_database(tables, engine)
        message = f"Loaded {rows_loaded:,} rows into RetailIQ warehouse."
        record_pipeline_run(engine, "success", message)
        return IngestResult("success", message, rows_loaded, run_at)
    except Exception as exc:
        try:
            record_pipeline_run(engine, "failed", str(exc))
        except Exception:
            pass
        return IngestResult("failed", str(exc), 0, run_at)


if __name__ == "__main__":
    result = run_pipeline()
    print(f"{result.status}: {result.message}")
