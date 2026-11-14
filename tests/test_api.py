"""SpendSense — FastAPI Endpoints Integration Tests"""

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


def test_serverless_entrypoint_routes():
    """Verify api/index.py serverless entrypoint matches both /api and root paths."""
    from api.index import app as serverless_app

    serverless_client = TestClient(serverless_app)

    res_root = serverless_client.get("/health")
    assert res_root.status_code == 200
    assert res_root.json()["status"] == "healthy"

    res_api = serverless_client.get("/api/health")
    assert res_api.status_code == 200
    assert res_api.json()["status"] == "healthy"

    res_ov = serverless_client.get("/api/overview")
    assert res_ov.status_code == 200
    assert res_ov.json()["total_transactions"] == 284807


def test_fraud_score_endpoint():
    """Verify POST /api/fraud/score real-time scoring engine and attribution."""
    from api.index import app as serverless_app

    serverless_client = TestClient(serverless_app)

    # 1. Safe Transaction Test
    safe_payload = {
        "cardholder_id": "CARD-48210",
        "amount": 34.50,
        "merchant_category": "Groceries & Supermarkets",
        "time_hour": 11,
        "velocity_last_24h": 1,
        "device_trust_score": 0.95,
        "is_cross_border": False,
    }
    safe_res = serverless_client.post("/api/fraud/score", json=safe_payload)
    assert safe_res.status_code == 200
    safe_data = safe_res.json()
    assert safe_data["decision"] == "APPROVED"
    assert safe_data["risk_tier"] == "LOW"
    assert safe_data["risk_score_pct"] < 5.0
    assert len(safe_data["factors"]) > 0

    # 2. Critical Fraud Outlier Test
    fraud_payload = {
        "cardholder_id": "CARD-33918",
        "amount": 4850.00,
        "merchant_category": "Online Retail & E-Commerce",
        "time_hour": 3,
        "velocity_last_24h": 12,
        "device_trust_score": 0.15,
        "is_cross_border": True,
    }
    fraud_res = serverless_client.post("/api/fraud/score", json=fraud_payload)
    assert fraud_res.status_code == 200
    fraud_data = fraud_res.json()
    assert fraud_data["decision"] in ["STEP_UP_AUTH", "DECLINED"]
    assert fraud_data["risk_tier"] in ["ELEVATED", "CRITICAL"]
    assert fraud_data["risk_score_pct"] >= 50.0
    assert any(f["factor"] == "Cross-Border Acquirer" for f in fraud_data["factors"])

