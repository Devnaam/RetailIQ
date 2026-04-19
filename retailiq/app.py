"""RetailIQ Streamlit application."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from retailiq.config import APP_NAME, DATABASE_URL
from retailiq.pipeline.download import download_olist_with_kagglehub
from retailiq.pipeline.ingest import run_pipeline
from retailiq.pipeline.transform import apply_filters, load_fact_orders
from retailiq.ui import customer_page, kpi_page, predict_page, product_page
from retailiq.ui.theme import apply_dark_theme


st.set_page_config(page_title=APP_NAME, page_icon="RIQ", layout="wide", initial_sidebar_state="expanded")
apply_dark_theme()


@st.cache_resource(show_spinner=False)
def create_engine_or_none():
    """Create the SQLAlchemy engine if database dependencies and connectivity are available."""

    try:
        from retailiq.pipeline.ingest import get_engine

        engine = get_engine(DATABASE_URL)
        with engine.connect():
            return engine
    except Exception:
        return None


@st.cache_data(show_spinner=False, ttl=600)
def get_dashboard_data() -> tuple[pd.DataFrame, datetime | None, str]:
    """Load and cache dashboard data."""

    engine = create_engine_or_none()
    return load_fact_orders(engine)


def sidebar_filters(df: pd.DataFrame) -> tuple[str, datetime, datetime, str, str]:
    """Render global sidebar controls."""

    st.sidebar.title("RetailIQ")
    page = st.sidebar.radio(
        "Navigation",
        ["Executive KPI Dashboard", "Customer Analytics", "Product & Seller Intelligence", "Predictive Analytics"],
    )

    min_date = df["order_purchase_timestamp"].min().date()
    max_date = df["order_purchase_timestamp"].max().date()
    selected_range = st.sidebar.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    if isinstance(selected_range, tuple) and len(selected_range) == 2:
        start_date, end_date = selected_range
    else:
        start_date, end_date = min_date, max_date

    categories = ["All", *sorted(df["product_category"].dropna().astype(str).unique())]
    states = ["All", *sorted(df["customer_state"].dropna().astype(str).unique())]
    category = st.sidebar.selectbox("Product category", categories)
    state = st.sidebar.selectbox("Brazilian state", states)

    st.sidebar.divider()
    if st.sidebar.button("Run CSV -> PostgreSQL pipeline", width="stretch"):
        with st.spinner("Running ingestion pipeline..."):
            result = run_pipeline()
        if result.status == "success":
            st.sidebar.success(result.message)
            st.cache_data.clear()
            st.cache_resource.clear()
        else:
            st.sidebar.error(result.message)

    if st.sidebar.button("Download Olist dataset", width="stretch"):
        with st.spinner("Downloading Olist dataset from KaggleHub..."):
            try:
                result = download_olist_with_kagglehub()
                st.sidebar.success(f"Copied {len(result.copied_files)} CSV files to {result.data_dir}")
                st.cache_data.clear()
                st.cache_resource.clear()
            except Exception as exc:
                st.sidebar.error(str(exc))

    return page, pd.to_datetime(start_date).to_pydatetime(), pd.to_datetime(end_date).to_pydatetime(), category, state


def main() -> None:
    """Run the RetailIQ dashboard."""

    with st.spinner("Fetching RetailIQ data..."):
        try:
            df, freshness, source = get_dashboard_data()
        except Exception as exc:
            st.error(str(exc))
            st.info("Use the sidebar download button, or run `python -m retailiq.pipeline.download` after installing KaggleHub.")
            return

    page, start_date, end_date, category, state = sidebar_filters(df)
    filtered = apply_filters(df, start_date, end_date, category, state)

    if freshness:
        freshness_text = freshness.strftime("%Y-%m-%d %H:%M:%S UTC")
    else:
        freshness_text = "No PostgreSQL pipeline run recorded"
    st.markdown(f"<div class='freshness'>Data source: {source} | Last pipeline run: {freshness_text}</div>", unsafe_allow_html=True)

    if filtered.empty:
        st.warning("No records match the selected filters.")
        return

    with st.spinner("Rendering analytics..."):
        if page == "Executive KPI Dashboard":
            kpi_page.render(filtered)
        elif page == "Customer Analytics":
            customer_page.render(filtered)
        elif page == "Product & Seller Intelligence":
            product_page.render(filtered)
        else:
            predict_page.render(filtered)


if __name__ == "__main__":
    main()
