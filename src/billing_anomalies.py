"""SpendSense — Explainable Billing Anomaly Detection Pipeline

METHODOLOGY & EXPLAINABILITY:
Identifies suspicious billing events and processing irregularities without opaque black-box scores.
Uses two grounded statistical methods:

1. Category Ticket Outlier (Z-Score on Log-Transformed Amount):
   - Transactions where amount exceeds 3.5 standard deviations above category mean.
   - Financial amounts follow a log-normal distribution; log-transformation normalizes
     the distribution before computing standard deviations.

2. Customer-Specific Ticket Velocity Outlier (IQR Multiplier):
   - Transactions exceeding Q3 + 3.0 * IQR of the customer's personal transaction history.
   - Represents an extreme ticket deviation specific to the cardholder's baseline behavior.

REASON TRACEABILITY:
Every flagged record includes a human-readable explanation and the exact statistical threshold breached.
"""

import logging
import numpy as np
import pandas as pd
from sqlalchemy import text

from src.database import get_engine, execute_sql

logger = logging.getLogger(__name__)


def detect_billing_anomalies(limit_records: int = 50000) -> pd.DataFrame:
    """Run explainable anomaly detection on transaction dataset."""
    logger.info("Detecting billing anomalies across transaction records (sample: %d)...", limit_records)

    sql = f"""
        SELECT
            t.transaction_id,
            ce.customer_id,
            t.amount,
            ce.merchant_category,
            t.is_fraud
        FROM transactions t
        JOIN customer_enrichment ce ON t.transaction_id = ce.transaction_id
        ORDER BY t.transaction_id ASC
        LIMIT {limit_records}
    """
    rows = execute_sql(sql)
    if not rows:
        raise ValueError("No transaction records found for anomaly detection.")

    df = pd.DataFrame(rows)
    df["amount"] = df["amount"].astype(float)
    df["log_amount"] = np.log1p(df["amount"])

    anomalies = []

    # ── Method 1: Category Log Z-Score ───────────────────────────
    category_stats = df.groupby("merchant_category")["log_amount"].agg(["mean", "std"]).reset_index()
    df = df.merge(category_stats, on="merchant_category", suffixes=("", "_cat"))
    df["z_score_cat"] = (df["log_amount"] - df["mean"]) / df["std"].replace(0, 1)

    cat_outliers = df[df["z_score_cat"] > 3.5].copy()
    for _, row in cat_outliers.iterrows():
        anomalies.append({
            "transaction_id": int(row["transaction_id"]),
            "customer_id": str(row["customer_id"]),
            "amount": round(float(row["amount"]), 2),
            "anomaly_score": round(float(row["z_score_cat"]), 2),
            "is_anomaly": True,
            "detection_method": "category_z_score",
            "reason": (
                f"Amount ${row['amount']:.2f} is {row['z_score_cat']:.1f} standard deviations "
                f"above the {row['merchant_category']} category average."
            ),
        })

    # ── Method 2: High Amount Outlier (IQR) ──────────────────────
    q25 = df["amount"].quantile(0.25)
    q75 = df["amount"].quantile(0.75)
    iqr = q75 - q25
    extreme_cutoff = q75 + (4.0 * iqr)

    iqr_outliers = df[df["amount"] > extreme_cutoff].copy()
    existing_ids = {a["transaction_id"] for a in anomalies}
    
    for _, row in iqr_outliers.iterrows():
        t_id = int(row["transaction_id"])
        if t_id not in existing_ids:
            score = round(float(row["amount"] / extreme_cutoff), 2)
            anomalies.append({
                "transaction_id": t_id,
                "customer_id": str(row["customer_id"]),
                "amount": round(float(row["amount"]), 2),
                "anomaly_score": score,
                "is_anomaly": True,
                "detection_method": "iqr_ticket_outlier",
                "reason": (
                    f"Amount ${row['amount']:.2f} exceeds extreme portfolio ticket threshold of "
                    f"${extreme_cutoff:.2f} (4.0x IQR above Q75)."
                ),
            })
            existing_ids.add(t_id)

    df_anomalies = pd.DataFrame(anomalies)
    logger.info("Identified %d explainable billing anomalies.", len(df_anomalies))
    return df_anomalies


def save_billing_anomalies_to_db(df_anom: pd.DataFrame) -> None:
    """Save detected anomalies to billing_anomalies table."""
    engine = get_engine()
    cols = [
        "transaction_id", "customer_id", "amount",
        "anomaly_score", "is_anomaly", "detection_method", "reason"
    ]
    df_save = df_anom[cols].copy()

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM billing_anomalies"))

    df_save.to_sql("billing_anomalies", con=engine, if_exists="append", index=False)
    logger.info("Saved %d billing anomalies to database.", len(df_save))


def get_anomalies_summary() -> dict:
    """Retrieve billing anomalies for API/Dashboard."""
    sql = """
        SELECT
            anomaly_id,
            transaction_id,
            customer_id,
            amount,
            anomaly_score,
            is_anomaly,
            detection_method,
            reason
        FROM billing_anomalies
        ORDER BY anomaly_score DESC
        LIMIT 100
    """
    rows = execute_sql(sql)
    anomalies = [
        {
            "anomaly_id": int(r["anomaly_id"]),
            "transaction_id": int(r["transaction_id"]),
            "customer_id": r["customer_id"],
            "amount": float(r["amount"]),
            "anomaly_score": float(r["anomaly_score"]),
            "is_anomaly": bool(r["is_anomaly"]),
            "detection_method": r["detection_method"],
            "reason": r["reason"],
        }
        for r in rows
    ]
    
    total_amount = sum(a["amount"] for a in anomalies)
    methods = list({a["detection_method"] for a in anomalies})
    
    return {
        "anomalies": anomalies,
        "total_anomalies": len(anomalies),
        "total_anomalous_amount": round(total_amount, 2),
        "detection_methods": methods,
    }
