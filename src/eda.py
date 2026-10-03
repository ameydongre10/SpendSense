"""SpendSense — Exploratory Data Analysis & Trend Analysis

Provides exploratory data analytics covering:
- Overall spend trends and transaction counts
- Merchant category mix
- Fraud rate distribution and time trends
- Distribution of transaction amounts (legitimate vs fraudulent)
"""

import logging
import pandas as pd
from src.database import execute_sql

logger = logging.getLogger(__name__)


def get_overview_statistics() -> dict:
    """Compute overall transaction and fraud statistics."""
    sql = """
        SELECT
            COUNT(*) AS total_transactions,
            SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) AS fraud_count,
            SUM(CASE WHEN is_fraud = 0 THEN 1 ELSE 0 END) AS legitimate_count,
            ROUND(100.0 * SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) / COUNT(*), 4) AS fraud_rate_pct,
            ROUND(SUM(amount), 2) AS total_amount,
            ROUND(SUM(CASE WHEN is_fraud = 1 THEN amount ELSE 0 END), 2) AS total_fraud_amount,
            ROUND(SUM(CASE WHEN is_fraud = 0 THEN amount ELSE 0 END), 2) AS total_legitimate_amount,
            ROUND(AVG(amount), 2) AS avg_transaction_amount,
            ROUND(AVG(CASE WHEN is_fraud = 1 THEN amount END), 2) AS avg_fraud_amount,
            ROUND(AVG(CASE WHEN is_fraud = 0 THEN amount END), 2) AS avg_legitimate_amount
        FROM transactions
    """
    rows = execute_sql(sql)
    if rows:
        row = rows[0]
        return {
            "total_transactions": int(row["total_transactions"]),
            "fraud_count": int(row["fraud_count"] or 0),
            "legitimate_count": int(row["legitimate_count"] or 0),
            "fraud_rate_pct": float(row["fraud_rate_pct"] or 0.0),
            "total_amount": float(row["total_amount"] or 0.0),
            "total_fraud_amount": float(row["total_fraud_amount"] or 0.0),
            "total_legitimate_amount": float(row["total_legitimate_amount"] or 0.0),
            "avg_transaction_amount": float(row["avg_transaction_amount"] or 0.0),
            "avg_fraud_amount": float(row["avg_fraud_amount"] or 0.0),
            "avg_legitimate_amount": float(row["avg_legitimate_amount"] or 0.0),
        }
    return {}


def get_monthly_fraud_trends() -> list[dict]:
    """Compute monthly transaction counts, fraud counts, and fraud rates over time."""
    sql = """
        SELECT
            SUBSTR(ce.transaction_date, 1, 7) AS period,
            COUNT(*) AS txn_count,
            SUM(CASE WHEN t.is_fraud = 1 THEN 1 ELSE 0 END) AS fraud_count,
            ROUND(100.0 * SUM(CASE WHEN t.is_fraud = 1 THEN 1 ELSE 0 END) / COUNT(*), 4) AS fraud_rate_pct,
            ROUND(SUM(CASE WHEN t.is_fraud = 1 THEN t.amount ELSE 0 END), 2) AS fraud_amount
        FROM transactions t
        JOIN customer_enrichment ce ON t.transaction_id = ce.transaction_id
        GROUP BY SUBSTR(ce.transaction_date, 1, 7)
        ORDER BY period ASC
    """
    rows = execute_sql(sql)
    return [
        {
            "period": r["period"],
            "txn_count": int(r["txn_count"]),
            "fraud_count": int(r["fraud_count"] or 0),
            "fraud_rate_pct": float(r["fraud_rate_pct"] or 0.0),
            "fraud_amount": float(r["fraud_amount"] or 0.0),
        }
        for r in rows
    ]


def get_spend_by_merchant_category() -> list[dict]:
    """Compute spend breakdown, average ticket size, and fraud rate per category."""
    sql = """
        SELECT
            ce.merchant_category,
            COUNT(*) AS txn_count,
            ROUND(SUM(t.amount), 2) AS total_spend,
            ROUND(AVG(t.amount), 2) AS avg_spend,
            SUM(CASE WHEN t.is_fraud = 1 THEN 1 ELSE 0 END) AS fraud_count,
            ROUND(100.0 * SUM(CASE WHEN t.is_fraud = 1 THEN 1 ELSE 0 END) / COUNT(*), 4) AS fraud_rate_pct
        FROM transactions t
        JOIN customer_enrichment ce ON t.transaction_id = ce.transaction_id
        GROUP BY ce.merchant_category
        ORDER BY total_spend DESC
    """
    rows = execute_sql(sql)
    return [
        {
            "category": r["merchant_category"],
            "txn_count": int(r["txn_count"]),
            "total_spend": float(r["total_spend"] or 0.0),
            "avg_spend": float(r["avg_spend"] or 0.0),
            "fraud_count": int(r["fraud_count"] or 0),
            "fraud_rate_pct": float(r["fraud_rate_pct"] or 0.0),
        }
        for r in rows
    ]
