"""SpendSense — Preprocessing & Feature Pipeline

Provides feature scaling, stratified train-test splitting, and feature preparation
for both baseline (Logistic Regression) and advanced (XGBoost) fraud models.
"""

import logging
from typing import Tuple
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler, StandardScaler

from src.database import execute_sql, get_connection

logger = logging.getLogger(__name__)


def load_dataset_for_modeling(limit: int | None = None) -> pd.DataFrame:
    """Load transaction features from database for ML training."""
    sql = """
        SELECT
            time_elapsed,
            v1, v2, v3, v4, v5, v6, v7, v8, v9, v10,
            v11, v12, v13, v14, v15, v16, v17, v18, v19, v20,
            v21, v22, v23, v24, v25, v26, v27, v28,
            amount, is_fraud
        FROM transactions
    """
    if limit:
        sql += f" LIMIT {limit}"
    
    records = execute_sql(sql)
    df = pd.DataFrame(records)
    logger.info("Loaded %d records for modeling. Fraud count: %d", len(df), df['is_fraud'].sum())
    return df


def prepare_features_and_target(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, list[str]]:
    """Extract feature matrix X and target array y with scaling on Amount and Time."""
    feature_cols = ["time_elapsed"] + [f"v{i}" for i in range(1, 29)] + ["amount"]
    
    # Scale Amount and Time (robust to heavy outliers in financial amounts)
    scaler_amount = RobustScaler()
    scaler_time = StandardScaler()
    
    scaled_amount = scaler_amount.fit_transform(df[["amount"]].values)
    scaled_time = scaler_time.fit_transform(df[["time_elapsed"]].values)
    
    # V1-V28 are already PCA scaled, so we retain them directly
    v_cols = [f"v{i}" for i in range(1, 29)]
    v_matrix = df[v_cols].values
    
    X = np.hstack([scaled_time, v_matrix, scaled_amount])
    y = df["is_fraud"].values.astype(int)
    
    return X, y, feature_cols


def get_stratified_train_test_split(
    X: np.ndarray,
    y: np.ndarray,
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Perform stratified train/test split to preserve ~0.17% fraud prevalence."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=y
    )
    logger.info(
        "Stratified Split: Train=%d (Frauds=%d, %.3f%%), Test=%d (Frauds=%d, %.3f%%)",
        len(y_train), int(y_train.sum()), (y_train.sum() / len(y_train)) * 100,
        len(y_test), int(y_test.sum()), (y_test.sum() / len(y_test)) * 100,
    )
    return X_train, X_test, y_train, y_test
