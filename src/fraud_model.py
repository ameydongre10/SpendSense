"""SpendSense — Fraud Risk Classification Pipeline

Implements the two required models:
1. Baseline Model: Logistic Regression (class_weight='balanced')
2. Advanced Model: XGBoost Classifier (scale_pos_weight parameter tuned for class imbalance)

Addresses severe class imbalance (~0.17% fraud prevalence) by penalizing false negatives
proportionally to the inverse class frequency. Evaluates models strictly on Precision,
Recall, and AUPRC (never raw accuracy).
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
import xgboost as xgb
from sqlalchemy import text

from src.config import Config
from src.database import get_engine, execute_sql
from src.preprocessing import (
    load_dataset_for_modeling,
    prepare_features_and_target,
    get_stratified_train_test_split,
)
from src.evaluation import evaluate_classifier_performance

logger = logging.getLogger(__name__)


def train_logistic_regression_baseline(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
) -> Tuple[LogisticRegression, Dict[str, Any]]:
    """Train baseline Logistic Regression with class-weight compensation."""
    logger.info("Training Baseline Logistic Regression with balanced class weights...")
    
    # Class weight='balanced' adjusts weights inversely proportional to class frequencies
    lr = LogisticRegression(
        class_weight="balanced",
        max_iter=1000,
        random_state=42,
        solver="lbfgs",
        C=0.1,
    )
    lr.fit(X_train, y_train)

    # Predict probabilities for positive class (fraud)
    y_pred_proba = lr.predict_proba(X_test)[:, 1]
    
    # Evaluate at optimal F1 threshold or standard 0.5
    eval_results = evaluate_classifier_performance(
        y_true=y_test,
        y_pred_proba=y_pred_proba,
        threshold=0.5,
        model_name="Logistic Regression (Baseline)",
    )
    eval_results["class_imbalance_strategy"] = "class_weight='balanced'"
    eval_results["training_samples"] = len(y_train)
    eval_results["test_samples"] = len(y_test)
    eval_results["notes"] = "Linear baseline with balanced class weights. Fast and interpretable."
    
    return lr, eval_results


def train_xgboost_advanced(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
) -> Tuple[xgb.XGBClassifier, Dict[str, Any]]:
    """Train advanced XGBoost model with scale_pos_weight for extreme class imbalance."""
    logger.info("Training Advanced XGBoost Classifier...")

    # Calculate scale_pos_weight: ratio of negative to positive samples
    n_neg = (y_train == 0).sum()
    n_pos = (y_train == 1).sum()
    scale_pos = float(n_neg / max(1, n_pos))
    logger.info("XGBoost scale_pos_weight set to %.2f (neg/pos ratio in train)", scale_pos)

    xgb_model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.08,
        scale_pos_weight=scale_pos,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="aucpr",
        random_state=42,
        n_jobs=-1,
    )
    xgb_model.fit(X_train, y_train)

    y_pred_proba = xgb_model.predict_proba(X_test)[:, 1]

    # Evaluate model
    eval_results = evaluate_classifier_performance(
        y_true=y_test,
        y_pred_proba=y_pred_proba,
        threshold=0.5,
        model_name="XGBoost (Advanced)",
    )
    eval_results["class_imbalance_strategy"] = f"scale_pos_weight={scale_pos:.1f}"
    eval_results["training_samples"] = len(y_train)
    eval_results["test_samples"] = len(y_test)
    eval_results["notes"] = "Gradient boosted decision trees capturing non-linear interactions across PCA components."

    return xgb_model, eval_results


def save_model_results_to_db(lr_eval: Dict[str, Any], xgb_eval: Dict[str, Any]) -> None:
    """Save model evaluation metrics to the model_results database table."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM model_results"))
        for res in [lr_eval, xgb_eval]:
            conn.execute(
                text("""
                    INSERT INTO model_results (
                        model_name, precision_score, recall_score, f1_score,
                        auprc, roc_auc, threshold, true_positives, false_positives,
                        true_negatives, false_negatives, class_imbalance_strategy,
                        training_samples, test_samples, notes
                    ) VALUES (
                        :model_name, :precision, :recall, :f1,
                        :auprc, :roc_auc, :threshold, :true_positives, :false_positives,
                        :true_negatives, :false_negatives, :class_imbalance_strategy,
                        :training_samples, :test_samples, :notes
                    )
                """),
                res
            )
    logger.info("Saved model evaluation results to database table model_results.")


def run_fraud_modeling_pipeline(limit: int | None = None) -> Dict[str, Any]:
    """Execute complete fraud modeling workflow: load -> split -> train -> evaluate -> persist."""
    logger.info("Starting complete Fraud Risk Modeling pipeline...")
    Config.ensure_directories()

    # 1. Load data
    df = load_dataset_for_modeling(limit=limit)
    X, y, feature_cols = prepare_features_and_target(df)

    # 2. Stratified train/test split
    X_train, X_test, y_train, y_test = get_stratified_train_test_split(X, y, test_size=0.2, random_state=42)

    # 3. Train Baseline (Logistic Regression)
    lr_model, lr_eval = train_logistic_regression_baseline(X_train, y_train, X_test, y_test)

    # 4. Train Advanced (XGBoost)
    xgb_model, xgb_eval = train_xgboost_advanced(X_train, y_train, X_test, y_test)

    # 5. Persist artifacts
    art_path = Config.MODEL_ARTIFACTS_PATH
    art_path.mkdir(parents=True, exist_ok=True)
    joblib.dump(lr_model, art_path / "logistic_regression.joblib")
    joblib.dump(xgb_model, art_path / "xgboost_model.joblib")

    # Save evaluation summary JSON
    summary = {
        "logistic_regression": lr_eval,
        "xgboost": xgb_eval,
        "feature_count": len(feature_cols),
        "target_fraud_count_test": int(y_test.sum()),
        "recommendation": (
            f"Deploy XGBoost: achieves AUPRC of {xgb_eval['auprc']:.4f} vs "
            f"{lr_eval['auprc']:.4f} for Logistic Regression, capturing complex "
            "non-linear fraud patterns while maintaining a high operational precision."
        ),
    }
    with open(art_path / "model_comparison.json", "w") as f:
        json.dump(summary, f, indent=2)

    # 6. Save to Database
    save_model_results_to_db(lr_eval, xgb_eval)

    logger.info("Fraud Modeling Pipeline completed successfully.")
    return summary
