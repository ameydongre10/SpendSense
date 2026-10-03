"""SpendSense — Cohort Retention & Lifecycle Analysis Pipeline

COHORT METHODOLOGY:
- Cohort Definition: Customers grouped by the calendar month of their initial transaction
  (cohort_month: e.g. 2023-01, 2023-02, ...).
- Observation Period: Calendar month of subsequent activity (period_month).
- Period Index: Integer index representing months elapsed (period 0 = acquisition month).
- Retention Metric: Active customer count in period N divided by initial cohort size (period 0).
- Spend Metric: Aggregate and average spend per active customer in each cohort period.

Provides actionable insight into customer lifetime value decay and retention velocity.
"""

import logging
import pandas as pd
from sqlalchemy import text

from src.database import get_engine, execute_sql

logger = logging.getLogger(__name__)


def compute_cohort_retention() -> pd.DataFrame:
    """Calculate monthly cohort retention and spend matrix."""
    logger.info("Computing cohort retention matrix...")
    
    sql = """
        SELECT
            ce.customer_id,
            SUBSTR(ce.transaction_date, 1, 7) AS txn_month,
            t.amount
        FROM customer_enrichment ce
        JOIN transactions t ON ce.transaction_id = t.transaction_id
    """
    rows = execute_sql(sql)
    if not rows:
        raise ValueError("No transaction records found for cohort analysis.")

    df = pd.DataFrame(rows)
    df["amount"] = df["amount"].astype(float)
    df["txn_date"] = pd.to_datetime(df["txn_month"] + "-01")

    # Determine cohort month (first transaction month for each customer)
    first_txns = df.groupby("customer_id")["txn_date"].min().reset_index()
    first_txns.columns = ["customer_id", "cohort_date"]
    
    df = df.merge(first_txns, on="customer_id")
    
    # Calculate period index (months elapsed between cohort_date and txn_date)
    year_diff = df["txn_date"].dt.year - df["cohort_date"].dt.year
    month_diff = df["txn_date"].dt.month - df["cohort_date"].dt.month
    df["period_index"] = year_diff * 12 + month_diff

    df["cohort_month"] = df["cohort_date"].dt.strftime("%Y-%m")
    df["period_month"] = df["txn_date"].dt.strftime("%Y-%m")

    # Aggregate by cohort_month and period_index
    cohort_group = df.groupby(["cohort_month", "period_month", "period_index"])
    cohort_data = cohort_group.agg(
        customer_count=("customer_id", "nunique"),
        total_spend=("amount", "sum"),
        avg_spend=("amount", "mean"),
    ).reset_index()

    # Determine initial cohort size (period_index == 0)
    cohort_sizes = cohort_data[cohort_data["period_index"] == 0].set_index("cohort_month")["customer_count"]
    
    cohort_data["initial_size"] = cohort_data["cohort_month"].map(cohort_sizes)
    cohort_data["retention_rate"] = (
        cohort_data["customer_count"] / cohort_data["initial_size"] * 100.0
    ).round(2)
    cohort_data["total_spend"] = cohort_data["total_spend"].round(2)
    cohort_data["avg_spend"] = cohort_data["avg_spend"].round(2)

    logger.info("Cohort matrix computed across %d cohort-period pairs.", len(cohort_data))
    return cohort_data


def save_cohort_analysis_to_db(df_cohort: pd.DataFrame) -> None:
    """Save computed cohort retention rows into cohort_analysis table."""
    engine = get_engine()
    cols = [
        "cohort_month", "period_month", "period_index",
        "customer_count", "retention_rate", "total_spend", "avg_spend"
    ]
    df_save = df_cohort[cols].copy()

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM cohort_analysis"))

    df_save.to_sql("cohort_analysis", con=engine, if_exists="append", index=False)
    logger.info("Saved %d cohort records into cohort_analysis table.", len(df_save))


def get_cohort_summary() -> dict:
    """Return cohort data formatted for dashboard visualization."""
    sql = """
        SELECT
            cohort_month,
            period_index,
            customer_count,
            retention_rate,
            total_spend
        FROM cohort_analysis
        ORDER BY cohort_month ASC, period_index ASC
    """
    rows = execute_sql(sql)
    cohort_months = sorted(list({r["cohort_month"] for r in rows}))
    max_periods = max([r["period_index"] for r in rows], default=0)

    cohorts = [
        {
            "cohort_month": r["cohort_month"],
            "period_index": int(r["period_index"]),
            "customer_count": int(r["customer_count"]),
            "retention_rate": float(r["retention_rate"] or 0.0),
            "total_spend": float(r["total_spend"] or 0.0),
        }
        for r in rows
    ]
    return {
        "cohorts": cohorts,
        "cohort_months": cohort_months,
        "max_periods": max_periods,
    }
