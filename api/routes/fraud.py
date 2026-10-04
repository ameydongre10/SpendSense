"""SpendSense — Fraud Risk Model & Trends API Routes

Exposes endpoints for:
- Monthly fraud rate and loss volume trends
- Logistic Regression baseline vs XGBoost advanced model comparison
- Precision-Recall curves, AUPRC, and decision recommendations
"""

import json
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException

from api.models import (
    FraudTrendsResponse,
    FraudTrendPoint,
    ModelComparisonResponse,
    ModelMetrics,
)
from src.config import Config
from src.eda import get_monthly_fraud_trends
from src.database import execute_sql

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/fraud", tags=["Fraud Risk Intelligence"])


@router.get("/trends", response_model=FraudTrendsResponse)
def get_fraud_trends():
    """Retrieve monthly fraud rate and loss trends over time."""
    try:
        trends = get_monthly_fraud_trends()
        if trends:
            return FraudTrendsResponse(
                trends=[FraudTrendPoint(**t) for t in trends]
            )
    except Exception as e:
        logger.warning("Error retrieving fraud trends from DB: %s, falling back to cache.", e)

    # Fallback to precomputed analytics cache
    cache_path = Config.PROJECT_ROOT / "analytics" / "cache" / "precomputed_analytics.json"
    if cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                c_data = json.load(f)
            cached_trends = c_data.get("trends", [])
            if cached_trends:
                return FraudTrendsResponse(
                    trends=[FraudTrendPoint(**t) for t in cached_trends]
                )
        except Exception:
            pass

    raise HTTPException(status_code=500, detail="Unable to retrieve fraud trends.")


@router.get("/model", response_model=ModelComparisonResponse)
def get_model_comparison():
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
                recommendation=data.get("recommendation", "Deploy XGBoost for optimal AUPRC."),
            )

        # Fallback to database table model_results
        sql = "SELECT * FROM model_results ORDER BY auprc DESC"
        rows = execute_sql(sql)
        if not rows:
            raise HTTPException(status_code=503, detail="Models not trained yet. Run pipeline first.")

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
                true_positives=int(r["true_positives"]) if r["true_positives"] else None,
                false_positives=int(r["false_positives"]) if r["false_positives"] else None,
                true_negatives=int(r["true_negatives"]) if r["true_negatives"] else None,
                false_negatives=int(r["false_negatives"]) if r["false_negatives"] else None,
                class_imbalance_strategy=r["class_imbalance_strategy"],
                training_samples=int(r["training_samples"]) if r["training_samples"] else None,
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
