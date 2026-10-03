"""SpendSense — RFM Customer Segmentation Pipeline

Calculates:
- Recency (R): Days from customer's most recent transaction to reference date
- Frequency (F): Total transaction count per customer
- Monetary (M): Total spend volume per customer

Scores each dimension on a 1-5 scale using robust quantiles.
Maps combined scores into actionable business segments:
- Champions (Highest value, frequent, recent)
- Loyal Spenders (Consistent high-value cardholders)
- Potential Enthusiasts (Recent, growing frequency)
- At-Risk High Value (High historical spend, declining recency)
- Hibernating / Dormant (Low recency, low engagement)
- Occasional Spenders (Low frequency, modest spend)
"""

import logging
from datetime import datetime
import numpy as np
import pandas as pd
from sqlalchemy import text

from src.database import get_engine, execute_sql

logger = logging.getLogger(__name__)


def compute_rfm_segments(reference_date: str = "2024-07-01") -> pd.DataFrame:
    """Extract customer transaction summaries and compute RFM metrics."""
    logger.info("Computing RFM metrics using reference date: %s", reference_date)
    
    sql = """
        SELECT
            ce.customer_id,
            COUNT(t.transaction_id) AS frequency,
            SUM(t.amount) AS monetary,
            MAX(ce.transaction_date) AS last_txn_date,
            MIN(ce.transaction_date) AS first_txn_date,
            SUM(CASE WHEN t.is_fraud = 1 THEN 1 ELSE 0 END) AS fraud_count
        FROM customer_enrichment ce
        JOIN transactions t ON ce.transaction_id = t.transaction_id
        GROUP BY ce.customer_id
    """
    rows = execute_sql(sql)
    if not rows:
        raise ValueError("No customer transaction records found. Run ingestion first.")

    df = pd.DataFrame(rows)
    ref_dt = pd.to_datetime(reference_date)
    df["last_txn_date"] = pd.to_datetime(df["last_txn_date"])
    df["recency_days"] = (ref_dt - df["last_txn_date"]).dt.days.clip(lower=0)
    
    # Clean monetary and frequency
    df["frequency"] = df["frequency"].astype(int)
    df["monetary"] = df["monetary"].astype(float)
    df["fraud_count"] = df["fraud_count"].astype(int)

    # Compute quintile scores (1 to 5)
    # Recency: lower days = higher score (5 is best)
    df["r_score"] = pd.qcut(df["recency_days"].rank(method="first", ascending=False), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    
    # Frequency: higher count = higher score (5 is best)
    df["f_score"] = pd.qcut(df["frequency"].rank(method="first", ascending=True), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    
    # Monetary: higher spend = higher score (5 is best)
    df["m_score"] = pd.qcut(df["monetary"].rank(method="first", ascending=True), 5, labels=[1, 2, 3, 4, 5]).astype(int)

    # Combined RFM Score
    df["rfm_score"] = df["r_score"] + df["f_score"] + df["m_score"]

    # Segment mapping based on R, F, M coordinates
    def assign_segment(row) -> str:
        r, f, m = row["r_score"], row["f_score"], row["m_score"]
        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"
        elif f >= 4 and m >= 3:
            return "Loyal Spenders"
        elif r >= 4 and f <= 3:
            return "Potential Enthusiasts"
        elif r <= 2 and (f >= 3 or m >= 4):
            return "At-Risk High Value"
        elif r <= 2 and f <= 2:
            return "Hibernating / Dormant"
        else:
            return "Occasional Spenders"

    df["segment_label"] = df.apply(assign_segment, axis=1)

    logger.info("RFM segmentation completed. Segment distribution:\n%s", df["segment_label"].value_counts())
    return df


def save_rfm_segments_to_db(df_rfm: pd.DataFrame) -> None:
    """Save computed RFM segments into rfm_segments table."""
    engine = get_engine()
    cols = [
        "customer_id", "recency_days", "frequency", "monetary",
        "r_score", "f_score", "m_score", "rfm_score", "segment_label"
    ]
    df_save = df_rfm[cols].copy()

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM rfm_segments"))

    df_save.to_sql("rfm_segments", con=engine, if_exists="append", index=False)
    logger.info("Saved %d RFM customer segments to database.", len(df_save))


def get_segment_aggregates() -> list[dict]:
    """Retrieve segment aggregate statistics for dashboard consumption."""
    sql = """
        SELECT
            r.segment_label,
            COUNT(r.customer_id) AS customer_count,
            ROUND(SUM(r.monetary), 2) AS total_spend,
            ROUND(AVG(r.monetary), 2) AS avg_spend,
            ROUND(AVG(r.frequency), 1) AS avg_frequency,
            ROUND(AVG(r.recency_days), 1) AS avg_recency_days,
            ROUND(100.0 * COUNT(r.customer_id) / (SELECT COUNT(*) FROM rfm_segments), 2) AS customer_share_pct
        FROM rfm_segments r
        GROUP BY r.segment_label
        ORDER BY total_spend DESC
    """
    rows = execute_sql(sql)
    total_spend = sum(float(r["total_spend"]) for r in rows) if rows else 1.0

    results = []
    for r in rows:
        t_spend = float(r["total_spend"])
        c_count = int(r["customer_count"])
        avg_sp = float(r["avg_spend"])
        
        # Calculate profitability proxy (normalized profit index)
        # Relative to average customer spend across portfolio
        results.append({
            "segment_label": r["segment_label"],
            "customer_count": c_count,
            "total_spend": t_spend,
            "avg_spend": avg_sp,
            "avg_frequency": float(r["avg_frequency"]),
            "avg_recency_days": float(r["avg_recency_days"]),
            "revenue_share": round((t_spend / total_spend) * 100, 2),
            "profit_index": round(avg_sp / 1000.0, 2),
        })
    return results
