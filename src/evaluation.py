"""SpendSense — Fraud Risk Model Evaluation Pipeline

METHODOLOGY & STATISTICAL RIGOR:
In fraud detection with extreme class imbalance (~0.17% fraud prevalence),
raw accuracy is a dangerously deceptive metric. A naive classifier predicting
0 for all transactions achieves 99.83% accuracy while failing to detect a single fraud.

MANDATORY METRICS:
1. Precision: TP / (TP + FP) — What fraction of flagged transactions are actual fraud?
   (Controls false-positive operational review costs and merchant/customer friction).
2. Recall: TP / (TP + FN) — What fraction of actual fraudulent events did we catch?
   (Directly protects revenue-at-risk).
3. AUPRC (Average Precision / PR-AUC): Primary ranking metric across all decision thresholds.
4. Precision at Target Recall (e.g. at 80% recall): Measures operational efficiency.
"""

import logging
from typing import Dict, Any, List, Tuple
import numpy as np
from sklearn.metrics import (
    precision_recall_curve,
    average_precision_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)

logger = logging.getLogger(__name__)


def evaluate_classifier_performance(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    threshold: float = 0.5,
    model_name: str = "Classifier",
) -> Dict[str, Any]:
    """Perform rigorous imbalanced classification evaluation."""
    y_pred = (y_pred_proba >= threshold).astype(int)

    # Confusion matrix
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    # Core metrics
    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    f1 = float(2 * (precision * recall) / (precision + recall)) if (precision + recall) > 0 else 0.0
    auprc = float(average_precision_score(y_true, y_pred_proba))
    roc_auc = float(roc_auc_score(y_true, y_pred_proba))

    # Precision-Recall Curve points for dashboard visualization (downsampled to 50 points)
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_pred_proba)
    step = max(1, len(recalls) // 50)
    pr_curve_sampled = [
        {"recall": round(float(recalls[i]), 4), "precision": round(float(precisions[i]), 4)}
        for i in range(0, len(recalls), step)
    ]

    # Evaluate Precision at 80% Recall target
    idx_80 = np.where(recalls >= 0.80)[0]
    precision_at_80_recall = float(precisions[idx_80[-1]]) if len(idx_80) > 0 else precision

    logger.info(
        "[%s] Evaluation Results (Threshold=%.2f): "
        "AUPRC=%.4f | Precision=%.4f | Recall=%.4f | F1=%.4f | TP=%d | FP=%d | FN=%d | TN=%d",
        model_name, threshold, auprc, precision, recall, f1, tp, fp, fn, tn
    )

    return {
        "model_name": model_name,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "auprc": round(auprc, 4),
        "roc_auc": round(roc_auc, 4),
        "threshold": round(threshold, 4),
        "true_positives": int(tp),
        "false_positives": int(fp),
        "true_negatives": int(tn),
        "false_negatives": int(fn),
        "precision_at_80_recall": round(precision_at_80_recall, 4),
        "pr_curve": pr_curve_sampled,
    }
