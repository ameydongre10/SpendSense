"""SpendSense — Security Headers, Anomaly Logic & Unit Economics Tests"""

from fastapi.testclient import TestClient

from api.main import app
from src.billing_anomalies import get_anomalies_summary
from src.profitability import get_profitability_summary

client = TestClient(app)


def test_security_headers_present():
    """Verify production security headers are attached to every API response."""
    response = client.get("/api/health")
    assert response.status_code == 200
    headers = response.headers

    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert "X-Process-Time-Ms" in headers
    assert "X-Request-ID" in headers
    assert "Content-Security-Policy" in headers


def test_fraud_score_input_validation():
    """Verify input validation bounds on POST /api/fraud/score."""
    # Test oversized merchant category (>64 chars)
    payload_oversized = {
        "cardholder_id": "CARD-001",
        "merchant_category": "A" * 100,
        "amount": 50.0,
    }
    res = client.post("/api/fraud/score", json=payload_oversized)
    assert res.status_code == 422

    # Test negative amount (<0.01)
    payload_neg = {
        "cardholder_id": "CARD-001",
        "merchant_category": "Online Retail & E-Commerce",
        "amount": -5.0,
    }
    res = client.post("/api/fraud/score", json=payload_neg)
    assert res.status_code == 422

    # Test valid payload with HTML chars in category gets escaped in factor description
    payload_html = {
        "cardholder_id": "CARD-001",
        "merchant_category": "Retail <script>",
        "amount": 75.0,
    }
    res = client.post("/api/fraud/score", json=payload_html)
    assert res.status_code == 200
    data = res.json()
    assert "<script>" not in str(data["factors"])
    assert "&lt;script&gt;" in str(data["factors"])


def test_invalid_endpoint_404():
    """Verify graceful 404 error responses for invalid endpoints."""
    response = client.get("/api/nonexistent_endpoint_xyz")
    assert response.status_code == 404


def test_billing_anomalies_summary_structure():
    """Verify statistical anomaly detection returns valid structure."""
    res = get_anomalies_summary()
    assert "total_anomalies" in res
    assert "detection_methods" in res
    assert "anomalies" in res
    assert len(res["detection_methods"]) >= 2
    if res["anomalies"]:
        sample = res["anomalies"][0]
        assert "transaction_id" in sample
        assert "amount" in sample
        assert "anomaly_score" in sample or "score" in sample
        assert "detection_method" in sample or "method" in sample


def test_profitability_summary_unit_economics():
    """Verify customer profitability unit economics calculations."""
    profs = get_profitability_summary()
    assert len(profs) > 0
    for p in profs:
        assert "segment_label" in p
        assert "customer_count" in p
        assert "profit_index" in p
        assert p["profit_index"] >= 0
