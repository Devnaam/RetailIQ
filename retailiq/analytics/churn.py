"""Customer churn modeling with Logistic Regression and optional SHAP explainability."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


FEATURE_COLUMNS = ["recency", "frequency", "monetary", "avg_review_score", "avg_delivery_days"]


def build_customer_features(df: pd.DataFrame, churn_days: int = 120) -> pd.DataFrame:
    """Build customer-level features and a churn label."""

    if df.empty:
        return pd.DataFrame(columns=["customer_unique_id", *FEATURE_COLUMNS, "churned"])

    snapshot = df["order_purchase_timestamp"].max() + pd.Timedelta(days=1)
    features = (
        df.groupby("customer_unique_id")
        .agg(
            recency=("order_purchase_timestamp", lambda x: (snapshot - x.max()).days),
            frequency=("order_id", "nunique"),
            monetary=("revenue", "sum"),
            avg_review_score=("review_score", "mean"),
            avg_delivery_days=("delivery_days", "mean"),
        )
        .reset_index()
    )
    features["avg_review_score"] = features["avg_review_score"].fillna(features["avg_review_score"].median())
    features["avg_delivery_days"] = features["avg_delivery_days"].fillna(features["avg_delivery_days"].median())
    features["churned"] = (features["recency"] > churn_days).astype(int)
    return features.replace([np.inf, -np.inf], 0).fillna(0)


def train_churn_model(customer_features: pd.DataFrame) -> dict[str, object]:
    """Train a churn classifier and return metrics, predictions, and drivers."""

    if customer_features.empty or customer_features["churned"].nunique() < 2:
        return {
            "metrics": {"F1": 0.0, "AUC-ROC": 0.0},
            "predictions": customer_features.assign(churn_probability=0.0),
            "drivers": pd.DataFrame({"feature": FEATURE_COLUMNS[:5], "importance": [0] * 5}),
        }

    x = customer_features[FEATURE_COLUMNS]
    y = customer_features["churned"]
    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x)
    stratify = y if y.value_counts().min() >= 2 else None
    x_train, x_test, y_train, y_test = train_test_split(x_scaled, y, test_size=0.25, random_state=42, stratify=stratify)
    model = LogisticRegression(max_iter=1000, class_weight="balanced")
    model.fit(x_train, y_train)
    probabilities = model.predict_proba(x_test)[:, 1]
    labels = (probabilities >= 0.5).astype(int)
    metrics = {
        "F1": float(f1_score(y_test, labels, zero_division=0)),
        "AUC-ROC": float(roc_auc_score(y_test, probabilities)) if y_test.nunique() > 1 else 0.0,
    }

    all_probabilities = model.predict_proba(x_scaled)[:, 1]
    predictions = customer_features.copy()
    predictions["churn_probability"] = all_probabilities

    drivers = _feature_importance(model, x_scaled)
    return {"metrics": metrics, "predictions": predictions, "drivers": drivers}


def _feature_importance(model: LogisticRegression, x_scaled: np.ndarray) -> pd.DataFrame:
    """Compute top churn drivers using SHAP when installed, else coefficients."""

    try:
        import shap

        explainer = shap.LinearExplainer(model, x_scaled)
        shap_values = explainer.shap_values(x_scaled)
        values = np.abs(shap_values).mean(axis=0)
        source = "mean_abs_shap"
    except Exception:
        values = np.abs(model.coef_[0])
        source = "abs_coefficient"

    return (
        pd.DataFrame({"feature": FEATURE_COLUMNS, "importance": values, "source": source})
        .sort_values("importance", ascending=False)
        .head(5)
    )
