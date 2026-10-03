"""SpendSense — Analytics API Routes

Exposes analytical endpoints backed by actual database and precomputed metrics:
- /api/overview
- /api/spend
- /api/segments
- /api/cohorts
- /api/profitability
- /api/anomalies
- /api/recommendations
"""

import logging
from fastapi import APIRouter, HTTPException

from api.models import (
    OverviewResponse,
    SpendAnalysisResponse,
    SpendByCategory,
    SegmentsResponse,
    SegmentDetail,
    CohortResponse,
    CohortRow,
    ProfitabilityResponse,
    ProfitabilityDetail,
    AnomaliesResponse,
    AnomalyDetail,
    RecommendationsResponse,
    Recommendation,
)
from src.eda import get_overview_statistics, get_spend_by_merchant_category
from src.rfm import get_segment_aggregates
from src.cohort import get_cohort_summary
from src.profitability import get_profitability_summary
from src.billing_anomalies import get_anomalies_summary
from src.recommendations import generate_business_recommendations
from src.database import execute_sql

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Analytics"])


@router.get("/overview", response_model=OverviewResponse)
def get_overview():
    """Retrieve top-level transaction and portfolio KPIs."""
    try:
        stats = get_overview_statistics()
        if not stats:
            raise HTTPException(status_code=503, detail="Analytics data not initialized. Run pipeline first.")

        # Query revenue-at-risk and entity counts from business_metrics
        b_metrics = execute_sql("SELECT metric_name, metric_value FROM business_metrics")
        m_map = {m["metric_name"]: float(m["metric_value"]) for m in b_metrics}

        return OverviewResponse(
            total_transactions=stats["total_transactions"],
            fraud_count=stats["fraud_count"],
            legitimate_count=stats["legitimate_count"],
            fraud_rate_pct=stats["fraud_rate_pct"],
            total_amount=stats["total_amount"],
            total_fraud_amount=stats["total_fraud_amount"],
            total_legitimate_amount=stats["total_legitimate_amount"],
            avg_transaction_amount=stats["avg_transaction_amount"],
            avg_fraud_amount=stats["avg_fraud_amount"],
            avg_legitimate_amount=stats["avg_legitimate_amount"],
            revenue_at_risk=m_map.get("revenue_at_risk_avoided", round(stats["total_fraud_amount"] * 0.85, 2)),
            unique_customers=int(m_map.get("unique_customers", 5000)),
            segment_count=int(m_map.get("segment_count", 6)),
            anomaly_count=int(m_map.get("billing_anomalies_count", 0)),
        )
    except Exception as e:
        logger.error("Error retrieving overview: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/spend", response_model=SpendAnalysisResponse)
def get_spend_analysis():
    """Retrieve spend volume and fraud distribution across merchant categories."""
    try:
        cats = get_spend_by_merchant_category()
        return SpendAnalysisResponse(categories=[SpendByCategory(**c) for c in cats])
    except Exception as e:
        logger.error("Error retrieving spend analysis: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/segments", response_model=SegmentsResponse)
def get_segments():
    """Retrieve RFM customer segments and aggregate metrics."""
    try:
        segs = get_segment_aggregates()
        total_cust = sum(s["customer_count"] for s in segs)
        return SegmentsResponse(
            segments=[SegmentDetail(**s) for s in segs],
            total_customers=total_cust,
        )
    except Exception as e:
        logger.error("Error retrieving segments: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cohorts", response_model=CohortResponse)
def get_cohorts():
    """Retrieve monthly cohort retention and spend matrix."""
    try:
        data = get_cohort_summary()
        return CohortResponse(
            cohorts=[CohortRow(**c) for c in data["cohorts"]],
            cohort_months=data["cohort_months"],
            max_periods=data["max_periods"],
        )
    except Exception as e:
        logger.error("Error retrieving cohorts: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profitability", response_model=ProfitabilityResponse)
def get_profitability():
    """Retrieve customer segment profitability analysis."""
    try:
        profs = get_profitability_summary()
        return ProfitabilityResponse(
            segments=[ProfitabilityDetail(**p) for p in profs]
        )
    except Exception as e:
        logger.error("Error retrieving profitability: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/anomalies", response_model=AnomaliesResponse)
def get_anomalies():
    """Retrieve explainable billing anomaly detection results."""
    try:
        data = get_anomalies_summary()
        return AnomaliesResponse(
            anomalies=[AnomalyDetail(**a) for a in data["anomalies"]],
            total_anomalies=data["total_anomalies"],
            total_anomalous_amount=data["total_anomalous_amount"],
            detection_methods=data["detection_methods"],
        )
    except Exception as e:
        logger.error("Error retrieving anomalies: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations", response_model=RecommendationsResponse)
def get_recommendations():
    """Retrieve the three quantified business recommendations."""
    try:
        recs = generate_business_recommendations()
        return RecommendationsResponse(
            recommendations=[Recommendation(**r) for r in recs]
        )
    except Exception as e:
        logger.error("Error retrieving recommendations: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
