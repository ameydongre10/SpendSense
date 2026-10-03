"""SpendSense — Canonical Metric Definitions

SINGLE SOURCE OF TRUTH for every metric used in the project.

Every metric is defined exactly once here. The analytics modules compute
these values, the API serves them, and the frontend displays them.
No metric is calculated differently in multiple layers.

Each metric has:
  - name        : unique identifier
  - display     : human-readable label for dashboard
  - formula     : how it is calculated
  - unit        : percent, dollars, count, score, ratio
  - source      : which table / computation produces it
  - category    : grouping for API/dashboard organization
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class MetricDefinition:
    """Immutable definition of a single canonical metric."""
    name: str
    display: str
    formula: str
    unit: str
    source: str
    category: str
    description: str = ""


# ════════════════════════════════════════════════
# CANONICAL METRIC REGISTRY
# ════════════════════════════════════════════════

METRICS: dict[str, MetricDefinition] = {}


def _register(m: MetricDefinition) -> MetricDefinition:
    METRICS[m.name] = m
    return m


# ── Overview Metrics ─────────────────────────

total_transactions = _register(MetricDefinition(
    name="total_transactions",
    display="Total Transactions",
    formula="COUNT(*) FROM transactions",
    unit="count",
    source="transactions",
    category="overview",
    description="Total number of card transactions in the dataset.",
))

fraud_count = _register(MetricDefinition(
    name="fraud_count",
    display="Fraudulent Transactions",
    formula="COUNT(*) FROM transactions WHERE is_fraud = 1",
    unit="count",
    source="transactions",
    category="overview",
))

fraud_rate = _register(MetricDefinition(
    name="fraud_rate",
    display="Fraud Rate",
    formula="fraud_count / total_transactions",
    unit="percent",
    source="transactions",
    category="overview",
    description="Percentage of transactions classified as fraudulent.",
))

total_fraud_amount = _register(MetricDefinition(
    name="total_fraud_amount",
    display="Total Fraud Amount",
    formula="SUM(amount) WHERE is_fraud = 1",
    unit="dollars",
    source="transactions",
    category="overview",
))

total_legitimate_amount = _register(MetricDefinition(
    name="total_legitimate_amount",
    display="Total Legitimate Amount",
    formula="SUM(amount) WHERE is_fraud = 0",
    unit="dollars",
    source="transactions",
    category="overview",
))

avg_transaction_amount = _register(MetricDefinition(
    name="avg_transaction_amount",
    display="Avg Transaction Amount",
    formula="AVG(amount)",
    unit="dollars",
    source="transactions",
    category="overview",
))

# ── Fraud Model Metrics ─────────────────────

precision_score = _register(MetricDefinition(
    name="precision",
    display="Precision",
    formula="TP / (TP + FP)",
    unit="ratio",
    source="model_results",
    category="model",
    description="Fraction of predicted frauds that are actual frauds.",
))

recall_score = _register(MetricDefinition(
    name="recall",
    display="Recall",
    formula="TP / (TP + FN)",
    unit="ratio",
    source="model_results",
    category="model",
    description="Fraction of actual frauds correctly detected.",
))

auprc_score = _register(MetricDefinition(
    name="auprc",
    display="AUPRC",
    formula="Area Under Precision-Recall Curve",
    unit="score",
    source="model_results",
    category="model",
    description="Primary evaluation metric for imbalanced classification.",
))

f1 = _register(MetricDefinition(
    name="f1",
    display="F1 Score",
    formula="2 * (precision * recall) / (precision + recall)",
    unit="score",
    source="model_results",
    category="model",
))

# ── Business Risk Metrics ────────────────────

revenue_at_risk = _register(MetricDefinition(
    name="revenue_at_risk",
    display="Revenue-at-Risk Avoided",
    formula="total_fraud_amount × model_recall",
    unit="dollars",
    source="model_results + transactions",
    category="business",
    description=(
        "Estimated dollar value of fraud successfully intercepted by the model. "
        "This is an ESTIMATE based on model recall applied to total fraud amount."
    ),
))

# ── Segmentation Metrics ─────────────────────

segment_count = _register(MetricDefinition(
    name="segment_count",
    display="Customer Segments",
    formula="COUNT(DISTINCT segment_label) FROM rfm_segments",
    unit="count",
    source="rfm_segments",
    category="segmentation",
))

segment_profitability_index = _register(MetricDefinition(
    name="segment_profitability",
    display="Segment Profitability Index",
    formula="segment_total_spend / segment_customer_count (relative index)",
    unit="index",
    source="segment_profitability",
    category="segmentation",
    description=(
        "Relative profitability index per segment. Based on average spend "
        "per customer as a proxy. Clearly an ASSUMPTION — real profitability "
        "would require cost/margin data not in this dataset."
    ),
))

# ── Anomaly Metrics ──────────────────────────

anomaly_count = _register(MetricDefinition(
    name="anomaly_count",
    display="Billing Anomalies Detected",
    formula="COUNT(*) FROM billing_anomalies WHERE is_anomaly = TRUE",
    unit="count",
    source="billing_anomalies",
    category="anomalies",
))

anomaly_total_amount = _register(MetricDefinition(
    name="anomaly_total_amount",
    display="Total Anomalous Amount",
    formula="SUM(amount) FROM billing_anomalies WHERE is_anomaly = TRUE",
    unit="dollars",
    source="billing_anomalies",
    category="anomalies",
))


def get_metrics_by_category(category: str) -> list[MetricDefinition]:
    """Return all metrics in a given category."""
    return [m for m in METRICS.values() if m.category == category]


def get_metric(name: str) -> Optional[MetricDefinition]:
    """Look up a metric by its canonical name."""
    return METRICS.get(name)
