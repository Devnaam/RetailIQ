"""SQLAlchemy models for the RetailIQ star schema."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for RetailIQ ORM models."""


class DimCustomer(Base):
    """Customer dimension."""

    __tablename__ = "dim_customers"

    customer_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_unique_id: Mapped[str] = mapped_column(String(64), index=True)
    zip_code_prefix: Mapped[int | None] = mapped_column(Integer, nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state: Mapped[str | None] = mapped_column(String(2), index=True, nullable=True)


class DimProduct(Base):
    """Product dimension."""

    __tablename__ = "dim_products"

    product_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    category: Mapped[str] = mapped_column(String(160), index=True, default="unknown")
    name_length: Mapped[float | None] = mapped_column(Float, nullable=True)
    description_length: Mapped[float | None] = mapped_column(Float, nullable=True)
    photos_qty: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    length_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    width_cm: Mapped[float | None] = mapped_column(Float, nullable=True)


class DimSeller(Base):
    """Seller dimension."""

    __tablename__ = "dim_sellers"

    seller_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    zip_code_prefix: Mapped[int | None] = mapped_column(Integer, nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state: Mapped[str | None] = mapped_column(String(2), index=True, nullable=True)


class FactOrder(Base):
    """Unified order fact table at order-item grain."""

    __tablename__ = "fact_orders"

    fact_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(String(64), index=True)
    order_item_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    customer_id: Mapped[str] = mapped_column(String(64), index=True)
    customer_unique_id: Mapped[str] = mapped_column(String(64), index=True)
    product_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    seller_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    order_status: Mapped[str] = mapped_column(String(40), index=True)
    customer_state: Mapped[str | None] = mapped_column(String(2), index=True, nullable=True)
    seller_state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    product_category: Mapped[str] = mapped_column(String(160), index=True, default="unknown")
    price: Mapped[float] = mapped_column(Float, default=0.0)
    freight_value: Mapped[float] = mapped_column(Float, default=0.0)
    revenue: Mapped[float] = mapped_column(Float, default=0.0)
    review_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    order_purchase_timestamp: Mapped[datetime | None] = mapped_column(DateTime, index=True, nullable=True)
    order_approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    order_delivered_carrier_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    order_delivered_customer_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    order_estimated_delivery_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    delivery_days: Mapped[float | None] = mapped_column(Float, nullable=True)


class PipelineRun(Base):
    """Pipeline metadata."""

    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    status: Mapped[str] = mapped_column(String(20), default="success")
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
