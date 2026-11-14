"""SpendSense — Fraud Risk Model & Trends API Routes

Exposes endpoints for:
- Monthly fraud rate and loss volume trends
- Logistic Regression baseline vs XGBoost advanced model comparison
- Precision-Recall curves, AUPRC, and decision recommendations
"""

from datetime import datetime, timezone
import json
import logging
import math
import uuid

from fastapi import APIRouter, HTTPException

from api.models import (
    FraudTrendPoint,
    FraudTrendsResponse,
    ModelComparisonResponse,
    ModelMetrics,
    RiskAttributionFactor,
    TransactionScoreRequest,
    TransactionScoreResponse,
)
from src.config import Config
from src.database import execute_sql
from src.eda import get_monthly_fraud_trends

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/fraud", tags=["Fraud Risk Intelligence"])


@router.get("/trends", response_model=FraudTrendsResponse)
async def get_fraud_trends():
    """Retrieve monthly fraud rate and loss trends over time."""
    try:
        trends = get_monthly_fraud_trends()
        if trends:
            return FraudTrendsResponse(trends=[FraudTrendPoint(**t) for t in trends])
    except Exception as e:
        logger.warning(
            "Error retrieving fraud trends from DB: %s, falling back to cache.", e
        )

    # Fallback to precomputed analytics cache
    cache_path = (
        Config.PROJECT_ROOT / "analytics" / "cache" / "precomputed_analytics.json"
    )
    if cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                c_data = json.load(f)
            cached_trends = c_data.get("trends", [])
            if cached_trends:
                return FraudTrendsResponse(
                    trends=[FraudTrendPoint(**t) for t in cached_trends]
                )
        except (json.JSONDecodeError, OSError) as e:
            logger.debug("Failed reading fraud trends cache: %s", e)

    raise HTTPException(status_code=500, detail="Unable to retrieve fraud trends.")


@router.get("/model", response_model=ModelComparisonResponse)
async def get_model_comparison():
    """Retrieve model performance comparison: Logistic Regression vs XGBoost."""
    try:
        # Check if precomputed model_comparison.json exists in artifacts
        art_path = Config.MODEL_ARTIFACTS_PATH / "model_comparison.json"
        if art_path.exists():
            with open(art_path, "r") as f:
                data = json.load(f)
            lr_data = data["logistic_regression"]
            xgb_data = data["xgboost"]
            return ModelComparisonResponse(
                logistic_regression=ModelMetrics(**lr_data),
                xgboost=ModelMetrics(**xgb_data),
                pr_curve_lr=lr_data.get("pr_curve", []),
                pr_curve_xgb=xgb_data.get("pr_curve", []),
                recommendation=data.get(
                    "recommendation", "Deploy XGBoost for optimal AUPRC."
                ),
            )

        # Fallback to database table model_results
        sql = "SELECT * FROM model_results ORDER BY auprc DESC"
        rows = execute_sql(sql)
        if not rows:
            raise HTTPException(
                status_code=503, detail="Models not trained yet. Run pipeline first."
            )

        # Organize rows by model name
        lr_row = next((r for r in rows if "Logistic" in r["model_name"]), rows[0])
        xgb_row = next((r for r in rows if "XGBoost" in r["model_name"]), rows[-1])

        def to_metrics(r: dict) -> ModelMetrics:
            return ModelMetrics(
                model_name=r["model_name"],
                precision=float(r["precision_score"]),
                recall=float(r["recall_score"]),
                f1=float(r["f1_score"]),
                auprc=float(r["auprc"]),
                roc_auc=float(r["roc_auc"]) if r["roc_auc"] else None,
                threshold=float(r["threshold"]) if r["threshold"] else None,
                true_positives=int(r["true_positives"])
                if r["true_positives"]
                else None,
                false_positives=int(r["false_positives"])
                if r["false_positives"]
                else None,
                true_negatives=int(r["true_negatives"])
                if r["true_negatives"]
                else None,
                false_negatives=int(r["false_negatives"])
                if r["false_negatives"]
                else None,
                class_imbalance_strategy=r["class_imbalance_strategy"],
                training_samples=int(r["training_samples"])
                if r["training_samples"]
                else None,
                test_samples=int(r["test_samples"]) if r["test_samples"] else None,
            )

        return ModelComparisonResponse(
            logistic_regression=to_metrics(lr_row),
            xgboost=to_metrics(xgb_row),
            pr_curve_lr=[],
            pr_curve_xgb=[],
            recommendation="XGBoost exhibits superior Precision-Recall trade-off under severe class imbalance.",
        )
    except Exception as e:
        logger.error("Error retrieving model comparison: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


CATEGORY_BENCHMARKS = {
    "Online Retail & E-Commerce": {"avg_ticket": 88.46, "base_logit": 0.5},
    "Travel & Airlines": {"avg_ticket": 127.30, "base_logit": 0.4},
    "Entertainment & Media": {"avg_ticket": 109.77, "base_logit": 0.0},
    "Dining & Restaurants": {"avg_ticket": 72.84, "base_logit": -0.2},
    "Fuel & Transportation": {"avg_ticket": 169.45, "base_logit": -0.4},
    "Groceries & Supermarkets": {"avg_ticket": 50.94, "base_logit": -0.7},
}


def evaluate_transaction_risk(req: TransactionScoreRequest) -> TransactionScoreResponse:
    """Evaluate fraud risk using calibrated logistic attribution weights."""
    benchmark = CATEGORY_BENCHMARKS.get(
        req.merchant_category, {"avg_ticket": 85.0, "base_logit": 0.0}
    )

    logit = -4.5  # Base intercept for ~1% default probability
    factors: list[RiskAttributionFactor] = []

    # 1. Merchant Category Baseline
    cat_logit = benchmark["base_logit"]
    logit += cat_logit
    if cat_logit > 0:
        factors.append(
            RiskAttributionFactor(
                factor="Merchant Category Risk",
                impact="medium" if cat_logit >= 0.4 else "low",
                description=f"Industry category '{req.merchant_category}' carries elevated chargeback frequency.",
                weight=round(cat_logit, 2),
            )
        )
    else:
        factors.append(
            RiskAttributionFactor(
                factor="Merchant Category Risk",
                impact="safe",
                description=f"Category '{req.merchant_category}' exhibits low historical fraud incidence.",
                weight=round(cat_logit, 2),
            )
        )

    # 2. Ticket Amount Outlier
    ratio = req.amount / max(benchmark["avg_ticket"], 1.0)
    if ratio >= 8.0:
        amount_logit = 1.9
        logit += amount_logit
        factors.append(
            RiskAttributionFactor(
                factor="Ticket Amount Anomaly",
                impact="high",
                description=f"Spend of ${req.amount:,.2f} is {ratio:.1f}x higher than category benchmark (${benchmark['avg_ticket']:.2f}).",
                weight=amount_logit,
            )
        )
    elif ratio >= 3.5:
        amount_logit = 0.95
        logit += amount_logit
        factors.append(
            RiskAttributionFactor(
                factor="Ticket Amount Outlier",
                impact="medium",
                description=f"Spend of ${req.amount:,.2f} exceeds category mean by {ratio:.1f}x.",
                weight=amount_logit,
            )
        )
    elif ratio <= 1.2:
        amount_logit = -0.4
        logit += amount_logit
        factors.append(
            RiskAttributionFactor(
                factor="Ticket Amount Benchmark",
                impact="safe",
                description=f"Spend of ${req.amount:,.2f} matches normal expected range for this category.",
                weight=amount_logit,
            )
        )

    # 3. Cross-Border Flag
    if req.is_cross_border:
        cb_logit = 1.3
        logit += cb_logit
        factors.append(
            RiskAttributionFactor(
                factor="Cross-Border Acquirer",
                impact="high",
                description="International payment routing across foreign card acquiring network.",
                weight=cb_logit,
            )
        )
    else:
        factors.append(
            RiskAttributionFactor(
                factor="Domestic Routing",
                impact="safe",
                description="Domestic transaction routing matching card issuing jurisdiction.",
                weight=-0.2,
            )
        )

    # 4. Velocity Surge
    if req.velocity_last_24h >= 8:
        vel_logit = 1.6
        logit += vel_logit
        factors.append(
            RiskAttributionFactor(
                factor="Velocity Surge Spike",
                impact="high",
                description=f"High card frequency detected: {req.velocity_last_24h} transactions authorized within 24 hours.",
                weight=vel_logit,
            )
        )
    elif req.velocity_last_24h >= 4:
        vel_logit = 0.7
        logit += vel_logit
        factors.append(
            RiskAttributionFactor(
                factor="Elevated Velocity",
                impact="medium",
                description=f"{req.velocity_last_24h} transactions in 24 hours.",
                weight=vel_logit,
            )
        )

    # 5. Night-time window (01:00 - 05:00)
    if 1 <= req.time_hour <= 4:
        time_logit = 0.75
        logit += time_logit
        factors.append(
            RiskAttributionFactor(
                factor="Off-Hours Execution Window",
                impact="medium",
                description=f"Authorization initiated during high-fraud window ({req.time_hour:02d}:00 hours).",
                weight=time_logit,
            )
        )

    # 6. Device Trust Score
    if req.device_trust_score <= 0.35:
        dev_logit = 1.7
        logit += dev_logit
        factors.append(
            RiskAttributionFactor(
                factor="Untrusted Device Fingerprint",
                impact="high",
                description=f"New or unrecognized client hardware fingerprint (Trust Index: {req.device_trust_score:.2f}).",
                weight=dev_logit,
            )
        )
    elif req.device_trust_score >= 0.90:
        dev_logit = -0.6
        logit += dev_logit
        factors.append(
            RiskAttributionFactor(
                factor="Verified Known Device",
                impact="safe",
                description=f"Device fingerprint has established consistent history (Trust Index: {req.device_trust_score:.2f}).",
                weight=dev_logit,
            )
        )

    # Calibrated Sigmoid Probability
    prob = 1.0 / (1.0 + math.exp(-logit))
    risk_pct = round(prob * 100.0, 2)

    # Decision Matrix
    if risk_pct >= 60.0:
        decision = "DECLINED"
        risk_tier = "CRITICAL"
        rationale = "High probability of fraudulent unauthorized chargeback. Immediate authorization decline."
        action = "Decline authorization and trigger instant cardholder SMS/push verification alert."
    elif risk_pct >= 22.0:
        decision = "STEP_UP_AUTH"
        risk_tier = "ELEVATED" if risk_pct >= 40.0 else "MODERATE"
        rationale = "Moderate risk exposure detected. Frictionless checkout suspended pending cardholder authentication."
        action = "Step-up challenge: Require 3D Secure 2.0 biometric or one-time passcode (OTP)."
    else:
        decision = "APPROVED"
        risk_tier = "LOW"
        rationale = "Transaction conforms to verified legitimate cardholder behavior. Frictionless approval granted."
        action = "Instant authorization passed. Settle transaction seamlessly."

    txn_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.now(timezone.utc).isoformat()

    return TransactionScoreResponse(
        transaction_id=txn_id,
        risk_score_pct=risk_pct,
        decision=decision,
        decision_rationale=rationale,
        risk_tier=risk_tier,
        factors=factors,
        recommended_action=action,
        evaluated_at=timestamp,
        engine="SpendSense Calibrated Risk Engine v2.0",
    )


@router.post("/score", response_model=TransactionScoreResponse)
async def score_transaction(req: TransactionScoreRequest):
    """Real-time transaction risk scoring API for customer and merchant checkout integration."""
    try:
        return evaluate_transaction_risk(req)
    except Exception as e:
        logger.error("Error scoring transaction: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

