"""SpendSense — End-to-End Pipeline Execution Script

Executes the complete financial analytics and machine learning pipeline:
1. Database Initialization
2. Transaction Ingestion & Validation
3. Synthetic Customer Profile Enrichment
4. RFM Customer Segmentation
5. Cohort Lifecycle & Retention Analysis
6. Customer Segment Profitability Modeling
7. Statistical Billing Anomaly Detection
8. Fraud Risk Classification (Logistic Regression baseline -> XGBoost advanced)
9. Business Risk Metrics & Revenue-at-Risk Computation
10. Data-Driven Recommendations Generation
"""

import argparse
import logging
import sys
import time
from pathlib import Path
import pandas as pd

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import Config
from src.database import init_db, check_connection, is_sqlite
from src.ingestion import load_raw_dataset, validate_and_clean_data, ingest_transactions_to_db
from src.synthetic_enrichment import generate_customer_enrichment, load_enrichment_to_db
from src.rfm import compute_rfm_segments, save_rfm_segments_to_db
from src.cohort import compute_cohort_retention, save_cohort_analysis_to_db
from src.profitability import compute_segment_profitability, save_segment_profitability_to_db
from src.billing_anomalies import detect_billing_anomalies, save_billing_anomalies_to_db
from src.fraud_model import run_fraud_modeling_pipeline
from src.business_metrics import compute_and_save_business_metrics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("SpendSense-Pipeline")


def run_pipeline(sample_size: int | None = None) -> None:
    """Execute end-to-end analytics and ML workflow."""
    start_time = time.time()
    logger.info("============================================================")
    logger.info("SPENDSENSE: END-TO-END ANALYTICS & ML PIPELINE STARTING")
    logger.info("============================================================")
    Config.ensure_directories()

    # Step 1: Database Initialization
    logger.info("--> [1/9] Initializing database tables and schema...")
    init_db()
    logger.info("Database active engine: %s", "SQLite (Embedded Fallback)" if is_sqlite() else "PostgreSQL")

    # Step 2: Ingestion & Validation
    logger.info("--> [2/9] Ingesting and validating raw transaction dataset...")
    df_raw = load_raw_dataset()
    if sample_size and len(df_raw) > sample_size:
        logger.info("Subsampling dataset to %d rows for rapid test execution...", sample_size)
        # Preserve all frauds in subsample for accurate balance representation
        df_frauds = df_raw[df_raw["Class"] == 1]
        df_legit = df_raw[df_raw["Class"] == 0].sample(n=sample_size - len(df_frauds), random_state=42)
        df_raw = pd.concat([df_legit, df_frauds]).sample(frac=1.0, random_state=42).reset_index(drop=True)

    df_clean = validate_and_clean_data(df_raw)
    n_txns = ingest_transactions_to_db(df_clean)

    # Step 3: Synthetic Customer Enrichment
    logger.info("--> [3/9] Applying synthetic customer profile enrichment (transparency enabled)...")
    df_enrichment = generate_customer_enrichment(n_transactions=n_txns, n_customers=Config.NUM_SYNTHETIC_CUSTOMERS)
    load_enrichment_to_db(df_enrichment)

    # Step 4: RFM Segmentation
    logger.info("--> [4/9] Calculating RFM customer segmentation and quintile scores...")
    df_rfm = compute_rfm_segments()
    save_rfm_segments_to_db(df_rfm)

    # Step 5: Cohort Retention Analysis
    logger.info("--> [5/9] Computing multi-period cohort retention matrix...")
    df_cohort = compute_cohort_retention()
    save_cohort_analysis_to_db(df_cohort)

    # Step 6: Segment Profitability Modeling
    logger.info("--> [6/9] Modeling customer segment profitability with payment network assumptions...")
    df_profitability = compute_segment_profitability()
    save_segment_profitability_to_db(df_profitability)

    # Step 7: Billing Anomaly Detection
    logger.info("--> [7/9] Running explainable billing anomaly detection...")
    df_anom = detect_billing_anomalies()
    save_billing_anomalies_to_db(df_anom)

    # Step 8: Fraud ML Classification (LR + XGBoost)
    logger.info("--> [8/9] Training and evaluating Logistic Regression and XGBoost classifiers...")
    model_summary = run_fraud_modeling_pipeline()

    # Step 9: Business Metrics & Revenue-at-Risk
    logger.info("--> [9/9] Computing portfolio risk metrics and revenue-at-risk avoided...")
    best_recall = model_summary["xgboost"]["recall"]
    business_metrics = compute_and_save_business_metrics(model_recall=best_recall)

    elapsed = time.time() - start_time
    logger.info("============================================================")
    logger.info("SPENDSENSE PIPELINE EXECUTION COMPLETED IN %.2f SECONDS", elapsed)
    logger.info("Total Transactions : %d", n_txns)
    logger.info("Fraud Rate         : %.4f%%", business_metrics["fraud_rate"])
    logger.info("Revenue-at-Risk    : $%.2f", business_metrics["revenue_at_risk_avoided"])
    logger.info("LR AUPRC           : %.4f", model_summary["logistic_regression"]["auprc"])
    logger.info("XGBoost AUPRC      : %.4f", model_summary["xgboost"]["auprc"])
    logger.info("============================================================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run SpendSense pipeline")
    parser.add_argument("--sample", type=int, default=None, help="Optional sample size for fast testing")
    args = parser.parse_args()
    run_pipeline(sample_size=args.sample)
