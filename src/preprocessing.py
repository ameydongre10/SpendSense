"""SpendSense — Preprocessing & Feature Pipeline

Provides feature scaling, stratified train-test splitting, and feature preparation
for both baseline (Logistic Regression) and advanced (XGBoost) fraud models.
"""

import logging

import numpy as np
import pandas as pd

try:
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import RobustScaler, StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

    class RobustScaler:
        def fit_transform(self, X):
            arr = np.asarray(X, dtype=float)
            med = np.median(arr, axis=0)
            q75, q25 = np.percentile(arr, [75, 25], axis=0)
            iqr = np.where((q75 - q25) == 0, 1.0, q75 - q25)
            return (arr - med) / iqr

    class StandardScaler:
        def fit_transform(self, X):
            arr = np.asarray(X, dtype=float)
            mean = np.mean(arr, axis=0)
            std = np.std(arr, axis=0)
            std = np.where(std == 0, 1.0, std)
            return (arr - mean) / std

    def train_test_split(X, y, test_size=0.2, stratify=None, random_state=None):
        if random_state is not None:
            np.random.seed(random_state)
        n = len(X)
        indices = np.arange(n)
        if stratify is not None:
            stratify = np.asarray(stratify)
            train_idx, test_idx = [], []
            for label in np.unique(stratify):
                label_indices = indices[stratify == label]
                np.random.shuffle(label_indices)
                split_point = int(len(label_indices) * (1 - test_size))
                train_idx.extend(label_indices[:split_point])
                test_idx.extend(label_indices[split_point:])
            train_idx = np.array(train_idx)
            test_idx = np.array(test_idx)
        else:
            np.random.shuffle(indices)
            split_point = int(n * (1 - test_size))
            train_idx = indices[:split_point]
            test_idx = indices[split_point:]

        if isinstance(X, pd.DataFrame):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        else:
            X_train, X_test = X[train_idx], X[test_idx]

        if isinstance(y, (pd.Series, pd.DataFrame)):
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        else:
            y_train, y_test = y[train_idx], y[test_idx]

        return X_train, X_test, y_train, y_test

from src.database import execute_sql

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
    logger.info(
        "Loaded %d records for modeling. Fraud count: %d", len(df), df["is_fraud"].sum()
    )
    return df


def prepare_features_and_target(
    df: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
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
    X: np.ndarray, y: np.ndarray, test_size: float = 0.2, random_state: int = 42
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Perform stratified train/test split to preserve ~0.17% fraud prevalence."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    logger.info(
        "Stratified Split: Train=%d (Frauds=%d, %.3f%%), Test=%d (Frauds=%d, %.3f%%)",
        len(y_train),
        int(y_train.sum()),
        (y_train.sum() / len(y_train)) * 100,
        len(y_test),
        int(y_test.sum()),
        (y_test.sum() / len(y_test)) * 100,
    )
    return X_train, X_test, y_train, y_test
