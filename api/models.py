"""SpendSense — API Response Models (Pydantic Contracts)

These are the FROZEN API contracts that both the backend and frontend
agree upon. The frontend is built against these shapes.

Changes to these models require coordinated backend + frontend updates.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ── Overview ─────────────────────────────────

class OverviewResponse(BaseModel):
    """GET /api/overview — top-level KPIs."""
    total_transactions: int
    fraud_count: int
    legitimate_count: int
    fraud_rate_pct: float = Field(description="Fraud rate as a percentage, e.g. 0.17")
    total_amount: float
    total_fraud_amount: float
    total_legitimate_amount: float
    avg_transaction_amount: float
    avg_fraud_amount: float
    avg_legitimate_amount: float
    revenue_at_risk: float = Field(description="Fraud amount × best model recall")
    unique_customers: int = Field(description="Distinct synthetic customer IDs")
    segment_count: int
    anomaly_count: int


# ── Fraud Trends ─────────────────────────────

class FraudTrendPoint(BaseModel):
    """Single data point in the fraud trend time series."""
    period: str = Field(description="YYYY-MM format")
    txn_count: int
    fraud_count: int
    fraud_rate_pct: float
    fraud_amount: float

class FraudTrendsResponse(BaseModel):
    trends: list[FraudTrendPoint]


# ── Fraud Model ──────────────────────────────

class ModelMetrics(BaseModel):
    """Evaluation metrics for a single fraud model."""
    model_name: str
    precision: float
    recall: float
    f1: float
    auprc: float
    roc_auc: Optional[float] = None
    threshold: Optional[float] = None
    true_positives: Optional[int] = None
    false_positives: Optional[int] = None
    true_negatives: Optional[int] = None
    false_negatives: Optional[int] = None
    class_imbalance_strategy: Optional[str] = None
    training_samples: Optional[int] = None
    test_samples: Optional[int] = None

class ModelComparisonResponse(BaseModel):
    """GET /api/fraud/model — LR vs XGBoost comparison."""
    logistic_regression: ModelMetrics
    xgboost: ModelMetrics
    pr_curve_lr: list[dict] = Field(default_factory=list, description="[{recall, precision}]")
    pr_curve_xgb: list[dict] = Field(default_factory=list, description="[{recall, precision}]")
    recommendation: str = Field(description="Which model and why")


# ── RFM Segments ─────────────────────────────

class SegmentDetail(BaseModel):
    """Single customer segment."""
    segment_label: str
    customer_count: int
    total_spend: float
    avg_spend: float
    avg_frequency: float
    avg_recency_days: float
    fraud_rate: Optional[float] = None
    profit_index: float
    revenue_share: float

class SegmentsResponse(BaseModel):
    """GET /api/segments — all RFM segments."""
    segments: list[SegmentDetail]
    total_customers: int


# ── Cohort Analysis ──────────────────────────

class CohortRow(BaseModel):
    """Single cell in the cohort retention matrix."""
    cohort_month: str
    period_index: int
    customer_count: int
    retention_rate: Optional[float] = None
    total_spend: Optional[float] = None

class CohortResponse(BaseModel):
    """GET /api/cohorts — cohort retention data."""
    cohorts: list[CohortRow]
    cohort_months: list[str]
    max_periods: int


# ── Profitability ────────────────────────────

class ProfitabilityDetail(BaseModel):
    """Profitability data for a single segment."""
    segment_label: str
    customer_count: int
    total_spend: float
    avg_spend: float
    avg_frequency: float
    fraud_rate: Optional[float] = None
    profit_index: float
    revenue_share: float

class ProfitabilityResponse(BaseModel):
    """GET /api/profitability — segment profitability."""
    segments: list[ProfitabilityDetail]
    methodology_note: str = Field(
        default=(
            "Profitability is estimated using average spend per customer as a proxy. "
            "Real profitability would require cost and margin data not available in "
            "this dataset. This is clearly an assumption."
        )
    )


# ── Billing Anomalies ───────────────────────

class AnomalyDetail(BaseModel):
    """Single detected billing anomaly."""
    anomaly_id: int
    transaction_id: int
    customer_id: Optional[str] = None
    amount: float
    anomaly_score: float
    is_anomaly: bool
    detection_method: str
    reason: Optional[str] = None

class AnomaliesResponse(BaseModel):
    """GET /api/anomalies — billing anomaly detection results."""
    anomalies: list[AnomalyDetail]
    total_anomalies: int
    total_anomalous_amount: float
    detection_methods: list[str]


# ── Spend Analysis ───────────────────────────

class SpendByCategory(BaseModel):
    category: str
    txn_count: int
    total_spend: float
    avg_spend: float
    fraud_count: int
    fraud_rate_pct: float

class SpendAnalysisResponse(BaseModel):
    """GET /api/spend — spend breakdown by merchant category."""
    categories: list[SpendByCategory]


# ── Business Recommendations ─────────────────

class Recommendation(BaseModel):
    """Single business recommendation."""
    id: int
    title: str
    finding: str
    evidence: str
    action: str
    quantified_impact: str
    priority: str = Field(description="high, medium, low")

class RecommendationsResponse(BaseModel):
    """GET /api/recommendations — data-driven recommendations."""
    recommendations: list[Recommendation]


# ── Health Check ─────────────────────────────

class HealthResponse(BaseModel):
    status: str
    database: str
    tables_loaded: dict[str, int]
