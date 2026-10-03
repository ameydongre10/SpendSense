"""SpendSense — Customer Segment Profitability Pipeline

PROFITABILITY MODELING METHODOLOGY:
In a modern payments card network (e.g. Mastercard, Visa, or closed-loop networks), cardholder
value is driven by spend volume (merchant discount / interchange revenue) minus network losses (fraud write-offs).

AVAILABLE DATA-DERIVED INPUTS:
- Total spend volume per segment ($)
- Total customer count per segment
- Average spend and transaction frequency
- Segment-level observed fraud loss ($)

ANALYTICAL ASSUMPTIONS (EXPLICITLY STATED):
1. Gross Network Take Rate: 2.50% of gross spend volume (standard premium credit card interchange/discount).
2. Fraud Net Loss: 100% of unrecovered fraudulent transactions attributed to segment.
3. Net Contribution Margin = (Spend Volume × 2.50%) - Fraud Losses.
4. Profit Index = (Segment Net Contribution / Customer Count) / Portfolio Benchmark Average.

This methodology mirrors how card issuer risk and product teams evaluate portfolio tier value.
"""

import logging
import pandas as pd
from sqlalchemy import text

from src.database import get_engine, execute_sql

logger = logging.getLogger(__name__)


def compute_segment_profitability() -> pd.DataFrame:
    """Calculate profitability metrics across RFM segments."""
    logger.info("Computing customer segment profitability metrics...")

    sql = """
        SELECT
            r.segment_label,
            COUNT(DISTINCT r.customer_id) AS customer_count,
            SUM(r.monetary) AS total_spend,
            AVG(r.monetary) AS avg_spend,
            AVG(r.frequency) AS avg_frequency
        FROM rfm_segments r
        GROUP BY r.segment_label
    """
    rows = execute_sql(sql)
    if not rows:
        raise ValueError("RFM segments table empty. Run compute_rfm_segments first.")

    df = pd.DataFrame(rows)
    df["customer_count"] = df["customer_count"].astype(int)
    df["total_spend"] = df["total_spend"].astype(float)
    df["avg_spend"] = df["avg_spend"].astype(float)
    df["avg_frequency"] = df["avg_frequency"].astype(float)

    # Calculate portfolio total spend
    portfolio_spend = df["total_spend"].sum()
    df["revenue_share"] = ((df["total_spend"] / portfolio_spend) * 100.0).round(2)

    # Get segment fraud stats
    fraud_sql = """
        SELECT
            r.segment_label,
            COALESCE(SUM(CASE WHEN t.is_fraud = 1 THEN t.amount ELSE 0 END), 0.0) AS fraud_amount,
            ROUND(100.0 * SUM(CASE WHEN t.is_fraud = 1 THEN 1 ELSE 0 END) / COUNT(t.transaction_id), 4) AS fraud_rate
        FROM rfm_segments r
        JOIN customer_enrichment ce ON r.customer_id = ce.customer_id
        JOIN transactions t ON ce.transaction_id = t.transaction_id
        GROUP BY r.segment_label
    """
    fraud_rows = execute_sql(fraud_sql)
    df_fraud = pd.DataFrame(fraud_rows) if fraud_rows else pd.DataFrame(columns=["segment_label", "fraud_amount", "fraud_rate"])

    if not df_fraud.empty:
        df = df.merge(df_fraud, on="segment_label", how="left")
        df["fraud_amount"] = df["fraud_amount"].fillna(0.0).astype(float)
        df["fraud_rate"] = df["fraud_rate"].fillna(0.0).astype(float)
    else:
        df["fraud_amount"] = 0.0
        df["fraud_rate"] = 0.0

    # Business Model Assumptions:
    # Gross Take Rate = 2.5%
    take_rate = 0.025
    df["gross_revenue"] = df["total_spend"] * take_rate
    df["net_contribution"] = df["gross_revenue"] - df["fraud_amount"]
    df["net_per_customer"] = df["net_contribution"] / df["customer_count"]

    # Normalize Profit Index relative to average customer net contribution
    portfolio_avg_contribution = df["net_contribution"].sum() / df["customer_count"].sum()
    df["profit_index"] = (df["net_per_customer"] / portfolio_avg_contribution).round(2)

    # Format values
    df["total_spend"] = df["total_spend"].round(2)
    df["avg_spend"] = df["avg_spend"].round(2)
    df["avg_frequency"] = df["avg_frequency"].round(1)

    logger.info("Profitability computed across %d segments:\n%s", len(df), df[["segment_label", "profit_index", "revenue_share"]])
    return df


def save_segment_profitability_to_db(df_prof: pd.DataFrame) -> None:
    """Save computed profitability records into segment_profitability table."""
    engine = get_engine()
    cols = [
        "segment_label", "customer_count", "total_spend", "avg_spend",
        "avg_frequency", "fraud_rate", "profit_index", "revenue_share"
    ]
    df_save = df_prof[cols].copy()

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM segment_profitability"))

    df_save.to_sql("segment_profitability", con=engine, if_exists="append", index=False)
    logger.info("Saved %d profitability records to database.", len(df_save))


def get_profitability_summary() -> list[dict]:
    """Retrieve segment profitability results for API/Dashboard."""
    sql = """
        SELECT
            segment_label,
            customer_count,
            total_spend,
            avg_spend,
            avg_frequency,
            fraud_rate,
            profit_index,
            revenue_share
        FROM segment_profitability
        ORDER BY profit_index DESC
    """
    rows = execute_sql(sql)
    return [
        {
            "segment_label": r["segment_label"],
            "customer_count": int(r["customer_count"]),
            "total_spend": float(r["total_spend"]),
            "avg_spend": float(r["avg_spend"]),
            "avg_frequency": float(r["avg_frequency"]),
            "fraud_rate": float(r["fraud_rate"] or 0.0),
            "profit_index": float(r["profit_index"]),
            "revenue_share": float(r["revenue_share"]),
        }
        for r in rows
    ]
