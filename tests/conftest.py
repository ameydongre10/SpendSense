"""SpendSense — Test Configuration & Pytest Fixtures

Ensures SQLite test database is properly initialized and seeded
for deterministic unit and integration test execution in CI/CD.
"""

import os
import pytest
from sqlalchemy import text

# Force SQLite mode for testing
os.environ["USE_SQLITE"] = "1"

from src.database import execute_sql, get_engine, init_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Session-scoped fixture to initialize schema and seed baseline test fixtures."""
    # Ensure tables exist
    init_db()

    # Seed transactions if empty
    res = execute_sql("SELECT COUNT(*) AS c FROM transactions")
    if not res or res[0]["c"] == 0:
        with get_engine().begin() as conn:
            # Seed sample transactions
            for i in range(1, 11):
                is_fraud = 1 if i <= 2 else 0
                amount = 120.0 if is_fraud else 45.0
                conn.execute(
                    text(
                        "INSERT INTO transactions (time_elapsed, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, "
                        "v11, v12, v13, v14, v15, v16, v17, v18, v19, v20, v21, v22, v23, v24, v25, v26, v27, v28, "
                        "amount, is_fraud) VALUES ("
                        f"{i * 10.0}, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "
                        "0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "
                        f"{amount}, {is_fraud})"
                    )
                )

            # Seed customer enrichment
            for i in range(1, 11):
                conn.execute(
                    text(
                        "INSERT INTO customer_enrichment (transaction_id, customer_id, transaction_date, merchant_category, city, state) "
                        f"VALUES ({i}, 'CUST_{i:03d}', '2024-01-{i:02d}', 'Dining', 'New York', 'NY')"
                    )
                )

            # Seed billing anomalies
            conn.execute(
                text(
                    "INSERT INTO billing_anomalies (transaction_id, customer_id, amount, anomaly_score, is_anomaly, detection_method, reason) "
                    "VALUES (1, 'CUST_001', 1200.0, 4.2, 1, 'Category Log Z-Score', 'Exceeds 3.5 std dev above Dining category mean')"
                )
            )
            conn.execute(
                text(
                    "INSERT INTO billing_anomalies (transaction_id, customer_id, amount, anomaly_score, is_anomaly, detection_method, reason) "
                    "VALUES (2, 'CUST_002', 2400.0, 5.1, 1, 'Customer IQR Multiplier', 'Exceeds 3x cardholder IQR threshold')"
                )
            )

            # Seed segment profitability
            conn.execute(
                text(
                    "INSERT INTO segment_profitability (segment_label, customer_count, total_spend, avg_spend, avg_frequency, fraud_rate, profit_index, revenue_share) "
                    "VALUES ('Champions', 500, 150000.0, 300.0, 12.0, 0.001, 165.4, 0.42)"
                )
            )
            conn.execute(
                text(
                    "INSERT INTO segment_profitability (segment_label, customer_count, total_spend, avg_spend, avg_frequency, fraud_rate, profit_index, revenue_share) "
                    "VALUES ('Loyal Spenders', 850, 120000.0, 141.0, 8.5, 0.0015, 128.2, 0.35)"
                )
            )

            # Seed model results
            conn.execute(
                text(
                    "INSERT INTO model_results (model_name, precision_score, recall_score, f1_score, auprc, roc_auc, threshold) "
                    "VALUES ('XGBoost', 0.88, 0.84, 0.86, 0.89, 0.98, 0.50)"
                )
            )
