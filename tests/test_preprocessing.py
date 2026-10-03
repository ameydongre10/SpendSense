"""SpendSense — Preprocessing & Feature Pipeline Unit Tests"""

import numpy as np
import pandas as pd
import pytest

from src.preprocessing import prepare_features_and_target, get_stratified_train_test_split


def test_prepare_features_and_target():
    # Mock transaction dataframe
    n = 100
    df = pd.DataFrame({
        "time_elapsed": np.linspace(0, 1000, n),
        **{f"v{i}": np.random.randn(n) for i in range(1, 29)},
        "amount": np.random.exponential(50, n),
        "is_fraud": np.random.choice([0, 1], size=n, p=[0.9, 0.1]),
    })
    
    X, y, cols = prepare_features_and_target(df)
    assert X.shape == (n, 30)
    assert len(y) == n
    assert len(cols) == 30
    assert "time_elapsed" in cols
    assert "amount" in cols


def test_stratified_train_test_split():
    n = 1000
    X = np.random.randn(n, 30)
    y = np.zeros(n, dtype=int)
    y[:20] = 1  # 2% fraud
    
    X_train, X_test, y_train, y_test = get_stratified_train_test_split(X, y, test_size=0.2, random_state=42)
    assert len(y_train) == 800
    assert len(y_test) == 200
    assert y_train.sum() == 16
    assert y_test.sum() == 4
