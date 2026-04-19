# RetailIQ - E-Commerce Intelligence Dashboard

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Warehouse-4169E1?logo=postgresql&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-Interactive_Charts-3F4F75?logo=plotly&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?logo=scikitlearn&logoColor=white)

RetailIQ is a full-stack business intelligence application for the Olist Brazilian E-Commerce public dataset. It loads raw marketplace CSVs into a PostgreSQL star schema, transforms them into analytics-ready facts and dimensions, and serves a dark-themed Streamlit dashboard with executive KPIs, customer segmentation, seller intelligence, and predictive churn and revenue analytics.

## Key Metrics Achieved

- Analyzes 100K+ Olist order records across customers, products, sellers, reviews, and order items.
- Builds a PostgreSQL warehouse with `fact_orders`, `dim_customers`, `dim_products`, `dim_sellers`, and pipeline freshness metadata.
- Identifies 4 customer segments with K-Means RFM clustering: Champions, Loyal, At Risk, and Lost.
- Produces monthly cohort retention, customer lifetime value, order status funnels, regional revenue maps, and product performance matrices.
- Trains a Logistic Regression churn model with F1 and AUC-ROC metrics shown in the dashboard.
- Explains churn drivers with SHAP values when SHAP is installed, with coefficient fallback for resilient local runs.
- Forecasts next-month revenue with Prophet when available, with an exponential smoothing fallback.

## Dashboard Pages

- Executive KPI Dashboard: total revenue in BRL, total orders, average order value, customer lifetime value, month-over-month deltas, 24-month revenue trend, top product categories, order funnel, and Brazilian state revenue map.
- Customer Analytics: RFM segmentation, 3D customer cluster view, churn probability by segment, cohort retention heatmap, and top customer lifetime value table.
- Product & Seller Intelligence: revenue versus review score matrix, seller leaderboard, review sentiment distribution, delivery time by region, and slow-moving inventory detection.
- Predictive Analytics: next-month revenue forecast, churn probability scoring, SHAP-style feature importance, and model accuracy metrics.

## Screenshots

<img width="1399" height="852" alt="image" src="https://github.com/user-attachments/assets/1f70b61e-723a-4d0b-9dde-044d9ac79294" />
<img width="1292" height="818" alt="image" src="https://github.com/user-attachments/assets/a56a183f-e619-435a-b6fa-4fcc3b645e73" />
<img width="1294" height="778" alt="image" src="https://github.com/user-attachments/assets/f944ecec-05e4-42a7-8abd-b85181f58c1f" />


## Project Structure

```text
retailiq/
├── app.py
├── config.py
├── pipeline/
│   ├── ingest.py
│   ├── transform.py
│   └── models.py
├── analytics/
│   ├── rfm.py
│   ├── forecast.py
│   ├── churn.py
│   └── cohort.py
└── ui/
    ├── kpi_page.py
    ├── customer_page.py
    ├── product_page.py
    ├── predict_page.py
    └── theme.py
```

## Dataset

Download the Olist Brazilian E-Commerce dataset from KaggleHub:

```powershell
pip install kagglehub
python -m retailiq.pipeline.download
```

That command copies the required CSVs into a local `data/` folder:

```text
data/
├── olist_orders_dataset.csv
├── olist_order_items_dataset.csv
├── olist_customers_dataset.csv
├── olist_products_dataset.csv
├── olist_sellers_dataset.csv
└── olist_order_reviews_dataset.csv
```

The dashboard expects real Olist data by default. To test the UI without downloaded CSVs, set `RETAILIQ_ALLOW_DEMO=true`.

## PostgreSQL Setup

Create a database and set `DATABASE_URL`:

```powershell
createdb retailiq
$env:DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/retailiq"
```

If `DATABASE_URL` is not set, the app uses:

```text
postgresql+psycopg2://postgres:postgres@localhost:5432/retailiq
```

## How To Run Locally

Install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the ingestion pipeline after placing CSV files in `data/`:

```powershell
python -m retailiq.pipeline.ingest
```

Start the dashboard:

```powershell
streamlit run app.py
```

Open the local Streamlit URL shown in the terminal. Use the sidebar button to rerun the CSV-to-PostgreSQL pipeline from inside the dashboard.

## Configuration

- `DATABASE_URL`: SQLAlchemy PostgreSQL connection string.
- `RETAILIQ_DATA_DIR`: optional path to the folder containing Olist CSV files.
- `RETAILIQ_MODEL_DIR`: optional path for future model artifacts.

## Resume Bullets

- Built RetailIQ, a full-stack Streamlit and PostgreSQL analytics dashboard for the Olist Brazilian E-Commerce dataset, analyzing 100K+ marketplace records.
- Designed a SQLAlchemy-powered warehouse pipeline with fact and dimension tables, data freshness tracking, date standardization, null handling, and BRL revenue calculations.
- Implemented executive BI dashboards with Plotly visualizations for revenue trends, product category performance, order funnels, and Brazilian state-level revenue distribution.
- Developed customer intelligence workflows using RFM feature engineering, K-Means clustering, monthly cohort retention, and customer lifetime value ranking.
- Created predictive analytics modules using Prophet revenue forecasting, Logistic Regression churn modeling, SHAP explainability, and live F1/AUC-ROC model metrics.
