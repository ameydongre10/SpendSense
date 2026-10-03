"""SpendSense — Model Evaluation & Metrics Unit Tests"""

import numpy as np
import pytest
from src.evaluation import evaluate_classifier_performance


def test_evaluate_classifier_metrics():
    # 100 samples with 10 true frauds
    y_true = np.zeros(100, dtype=int)
    y_true[:10] = 1
    
    # Predict high probabilities for true frauds and low for legit
    y_pred_proba = np.zeros(100)
    y_pred_proba[:8] = 0.9   # 8 True Positives
    y_pred_proba[8:10] = 0.2 # 2 False Negatives
    y_pred_proba[10:12] = 0.8 # 2 False Positives
    y_pred_proba[12:] = 0.1  # 88 True Negatives
    
    eval_res = evaluate_classifier_performance(y_true, y_pred_proba, threshold=0.5, model_name="TestModel")
    
    assert eval_res["true_positives"] == 8
    assert eval_res["false_positives"] == 2
    assert eval_res["false_negatives"] == 2
    assert eval_res["true_negatives"] == 88
    
    # Precision = 8 / (8 + 2) = 0.8
    assert eval_res["precision"] == 0.8
    # Recall = 8 / (8 + 2) = 0.8
    assert eval_res["recall"] == 0.8
    # AUPRC should be reasonably high
    assert eval_res["auprc"] > 0.5
    assert len(eval_res["pr_curve"]) > 0
