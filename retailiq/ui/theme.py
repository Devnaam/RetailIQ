"""UI styling and shared Plotly helpers."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from retailiq.config import COLOR_SEQUENCE, PLOTLY_TEMPLATE


def apply_dark_theme() -> None:
    """Inject RetailIQ custom CSS."""

    st.markdown(
        """
        <style>
        :root {
            --riq-bg: #070b11;
            --riq-panel: #101822;
            --riq-border: #253244;
            --riq-text: #eef4ff;
            --riq-muted: #9caec4;
            --riq-accent: #00d4ff;
            --riq-good: #34d399;
            --riq-bad: #f87171;
        }
        .stApp {
            background: var(--riq-bg);
            color: var(--riq-text);
        }
        section[data-testid="stSidebar"] {
            background: #0b1119;
            border-right: 1px solid var(--riq-border);
        }
        div[data-testid="stMetric"] {
            background: var(--riq-panel);
            border: 1px solid var(--riq-border);
            border-radius: 8px;
            padding: 16px;
            min-height: 122px;
        }
        div[data-testid="stMetric"] label, .muted {
            color: var(--riq-muted) !important;
        }
        .riq-card {
            background: var(--riq-panel);
            border: 1px solid var(--riq-border);
            border-radius: 8px;
            padding: 14px 16px;
        }
        .freshness {
            color: var(--riq-muted);
            font-size: 0.9rem;
        }
        h1, h2, h3 {
            letter-spacing: 0;
        }
        @media (max-width: 768px) {
            div[data-testid="stMetric"] {
                min-height: auto;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_figure(fig: go.Figure, height: int = 420) -> go.Figure:
    """Apply common dashboard figure styling."""

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        colorway=COLOR_SEQUENCE,
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=50, b=30),
        font=dict(color="#eef4ff"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig
