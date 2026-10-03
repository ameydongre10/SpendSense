"""SpendSense — FastAPI Endpoints Integration Tests"""

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "tables_loaded" in data


def test_overview_endpoint():
    response = client.get("/api/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["total_transactions"] > 0
    assert "fraud_rate_pct" in data
    assert "revenue_at_risk" in data
    assert data["revenue_at_risk"] > 0


def test_spend_analysis_endpoint():
    response = client.get("/api/spend")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert len(data["categories"]) > 0
    cat = data["categories"][0]
    assert "category" in cat
    assert "total_spend" in cat


def test_segments_endpoint():
    response = client.get("/api/segments")
    assert response.status_code == 200
    data = response.json()
    assert "segments" in data
    assert len(data["segments"]) > 0
    seg = data["segments"][0]
    assert "segment_label" in seg
    assert "profit_index" in seg


def test_cohorts_endpoint():
    response = client.get("/api/cohorts")
    assert response.status_code == 200
    data = response.json()
    assert "cohorts" in data
    assert "cohort_months" in data


def test_profitability_endpoint():
    response = client.get("/api/profitability")
    assert response.status_code == 200
    data = response.json()
    assert "segments" in data
    assert len(data["segments"]) > 0


def test_anomalies_endpoint():
    response = client.get("/api/anomalies")
    assert response.status_code == 200
    data = response.json()
    assert "anomalies" in data
    assert "detection_methods" in data


def test_fraud_trends_endpoint():
    response = client.get("/api/fraud/trends")
    assert response.status_code == 200
    data = response.json()
    assert "trends" in data
    assert len(data["trends"]) > 0


def test_fraud_model_endpoint():
    response = client.get("/api/fraud/model")
    assert response.status_code == 200
    data = response.json()
    assert "logistic_regression" in data
    assert "xgboost" in data
    assert data["xgboost"]["auprc"] > 0
    assert data["logistic_regression"]["auprc"] > 0


def test_recommendations_endpoint():
    response = client.get("/api/recommendations")
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert len(data["recommendations"]) == 3
