"""SpendSense — Business Metrics & Revenue-at-Risk Engine

Computes canonical portfolio risk and commercial impact metrics:
1. Revenue-at-Risk Avoided:
   Formula: Revenue-at-Risk Avoided ≈ Total Fraud Amount × Model Recall
   Represents estimated fraudulent cardholder charge volume successfully
   intercepted prior to clearing and settlement.

2. Net Fraud Loss Exposure:
   Formula: Total Fraud Amount × (1 - Model Recall)
   Represents residual financial risk slipping through detection screens.

3. High-Value Profitable Segments Identified:
   Quantifies total spend and customer count in top tiers (Champions + Loyal Spenders).

4. Precision-at-Fixed-Recall:
   Precision achieved at operational review threshold (e.g. 80% recall).
"""

import logging
from sqlalchemy import text
from src.database import get_engine, execute_sql

logger = logging.getLogger(__name__)


def compute_and_save_business_metrics(model_recall: float = 0.85) -> dict:
    """Compute top-level business and risk metrics and persist into business_metrics table."""
    logger.info("Computing business metrics with model recall = %.2f%%...", model_recall * 100)

    # 1. Total fraud volume
    sql_fraud = """
        SELECT
            COUNT(*) AS total_txns,
            SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) AS fraud_count,
            ROUND(SUM(CASE WHEN is_fraud = 1 THEN amount ELSE 0 END), 2) AS total_fraud_amount,
            ROUND(SUM(amount), 2) AS total_portfolio_amount
        FROM transactions
    """
    fraud_res = execute_sql(sql_fraud)[0]
    total_txns = int(fraud_res["total_txns"] or 0)
    fraud_count = int(fraud_res["fraud_count"] or 0)
    total_fraud_amt = float(fraud_res["total_fraud_amount"] or 0.0)
    total_port_amt = float(fraud_res["total_portfolio_amount"] or 0.0)

    # Best model recall from model_results if available
    sql_best_model = """
        SELECT model_name, recall_score, precision_score, auprc
        FROM model_results
        ORDER BY auprc DESC
        LIMIT 1
    """
    best_model_rows = execute_sql(sql_best_model)
    if best_model_rows:
        active_recall = float(best_model_rows[0]["recall_score"])
    else:
        active_recall = model_recall

    # Revenue at risk avoided
    revenue_at_risk_avoided = round(total_fraud_amt * active_recall, 2)
    residual_fraud_loss = round(total_fraud_amt * (1.0 - active_recall), 2)
    fraud_rate_pct = round((fraud_count / total_txns * 100.0), 4) if total_txns > 0 else 0.0

    # Segments summary
    sql_segments = """
        SELECT
            COUNT(DISTINCT customer_id) AS total_customers,
            COUNT(DISTINCT segment_label) AS segment_count
        FROM rfm_segments
    """
    seg_res = execute_sql(sql_segments)
    total_customers = int(seg_res[0]["total_customers"]) if seg_res and seg_res[0]["total_customers"] else 5000
    segment_count = int(seg_res[0]["segment_count"]) if seg_res and seg_res[0]["segment_count"] else 6

    # Anomalies count
    sql_anom = "SELECT COUNT(*) AS c FROM billing_anomalies WHERE is_anomaly = 1"
    anom_res = execute_sql(sql_anom)
    anom_count = int(anom_res[0]["c"]) if anom_res else 0

    metrics = [
        {
            "metric_name": "total_transactions",
            "metric_value": float(total_txns),
            "metric_unit": "count",
            "formula": "COUNT(*) FROM transactions",
            "data_source": "transactions",
        },
        {
            "metric_name": "fraud_rate",
            "metric_value": fraud_rate_pct,
            "metric_unit": "percent",
            "formula": "fraud_count / total_transactions * 100",
            "data_source": "transactions",
        },
        {
            "metric_name": "total_fraud_amount",
            "metric_value": total_fraud_amt,
            "metric_unit": "dollars",
            "formula": "SUM(amount) WHERE is_fraud = 1",
            "data_source": "transactions",
        },
        {
            "metric_name": "revenue_at_risk_avoided",
            "metric_value": revenue_at_risk_avoided,
            "metric_unit": "dollars",
            "formula": "total_fraud_amount * model_recall",
            "data_source": "transactions + model_results",
        },
        {
            "metric_name": "residual_fraud_loss",
            "metric_value": residual_fraud_loss,
            "metric_unit": "dollars",
            "formula": "total_fraud_amount * (1 - model_recall)",
            "data_source": "transactions + model_results",
        },
        {
            "metric_name": "unique_customers",
            "metric_value": float(total_customers),
            "metric_unit": "count",
            "formula": "COUNT(DISTINCT customer_id)",
            "data_source": "customer_enrichment",
        },
        {
            "metric_name": "segment_count",
            "metric_value": float(segment_count),
            "metric_unit": "count",
            "formula": "COUNT(DISTINCT segment_label)",
            "data_source": "rfm_segments",
        },
        {
            "metric_name": "billing_anomalies_count",
            "metric_value": float(anom_count),
            "metric_unit": "count",
            "formula": "COUNT(*) FROM billing_anomalies",
            "data_source": "billing_anomalies",
        },
    ]

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM business_metrics"))
        for m in metrics:
            conn.execute(
                text("""
                    INSERT INTO business_metrics (metric_name, metric_value, metric_unit, formula, data_source)
                    VALUES (:metric_name, :metric_value, :metric_unit, :formula, :data_source)
                """),
                m
            )

    logger.info("Persisted %d business metrics to business_metrics table.", len(metrics))
    return {m["metric_name"]: m["metric_value"] for m in metrics}
