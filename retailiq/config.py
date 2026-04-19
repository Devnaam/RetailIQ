"""Shared configuration for RetailIQ."""

from __future__ import annotations

import os
from pathlib import Path


APP_NAME = "RetailIQ - E-Commerce Intelligence Dashboard"
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = Path(os.getenv("RETAILIQ_DATA_DIR", PROJECT_ROOT / "data"))
MODEL_DIR = Path(os.getenv("RETAILIQ_MODEL_DIR", PROJECT_ROOT / "models"))
ALLOW_DEMO_DATA = os.getenv("RETAILIQ_ALLOW_DEMO", "false").lower() in {"1", "true", "yes"}

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/retailiq",
)

DATE_COLUMN = "order_purchase_timestamp"
BR_STATES = [
    "AC",
    "AL",
    "AM",
    "AP",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MG",
    "MS",
    "MT",
    "PA",
    "PB",
    "PE",
    "PI",
    "PR",
    "RJ",
    "RN",
    "RO",
    "RR",
    "RS",
    "SC",
    "SE",
    "SP",
    "TO",
]

PLOTLY_TEMPLATE = "plotly_dark"
COLOR_SEQUENCE = ["#00d4ff", "#34d399", "#f59e0b", "#f87171", "#a78bfa", "#f472b6"]
