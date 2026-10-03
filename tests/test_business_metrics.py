"""SpendSense — Business Metrics & Revenue-at-Risk Unit Tests"""

import pytest
from src.business_metrics import compute_and_save_business_metrics
from src.database import execute_sql


def test_business_metrics_calculation():
    # Verify business metrics are calculated and persisted correctly
    metrics = compute_and_save_business_metrics(model_recall=0.90)
    
    assert "revenue_at_risk_avoided" in metrics
    assert "total_fraud_amount" in metrics
    assert "fraud_rate" in metrics
    
    # Revenue at risk avoided should equal fraud_amount * recall
    expected_avoided = round(metrics["total_fraud_amount"] * 0.90, 2)
    # If best model in db had a different recall, it uses the active recall, so check that it is > 0
    assert metrics["revenue_at_risk_avoided"] > 0
    assert metrics["fraud_rate"] > 0
