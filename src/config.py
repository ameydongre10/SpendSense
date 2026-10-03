"""SpendSense — Application Configuration

Centralizes all environment-based configuration.
Every module reads from this single source.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


class Config:
    """Application configuration from environment variables."""

    # ── PostgreSQL ───────────────────────────
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "spendsense")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "spendsense_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")

    @classmethod
    def database_url(cls) -> str:
        return (
            f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}"
            f"@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
        )

    # ── Application ──────────────────────────
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # ── Paths ────────────────────────────────
    PROJECT_ROOT: Path = _PROJECT_ROOT
    RAW_DATA_PATH: Path = _PROJECT_ROOT / os.getenv("RAW_DATA_PATH", "data/raw/creditcard.csv")
    PROCESSED_DATA_PATH: Path = _PROJECT_ROOT / os.getenv("PROCESSED_DATA_PATH", "data/processed")
    MODEL_ARTIFACTS_PATH: Path = _PROJECT_ROOT / os.getenv("MODEL_ARTIFACTS_PATH", "ml/artifacts")
    ANALYTICS_CACHE_PATH: Path = _PROJECT_ROOT / os.getenv("ANALYTICS_CACHE_PATH", "analytics/cache")

    @classmethod
    def ensure_directories(cls) -> None:
        """Create required directories if they don't exist."""
        for path in [
            cls.PROCESSED_DATA_PATH,
            cls.MODEL_ARTIFACTS_PATH,
            cls.ANALYTICS_CACHE_PATH,
            cls.RAW_DATA_PATH.parent,
        ]:
            path.mkdir(parents=True, exist_ok=True)

    # ── Dataset Constants ────────────────────
    # Kaggle Credit Card Fraud Detection dataset
    EXPECTED_COLUMNS: list[str] = [
        "Time", "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9",
        "V10", "V11", "V12", "V13", "V14", "V15", "V16", "V17", "V18",
        "V19", "V20", "V21", "V22", "V23", "V24", "V25", "V26", "V27",
        "V28", "Amount", "Class",
    ]
    EXPECTED_ROW_COUNT_MIN: int = 280_000
    EXPECTED_FRAUD_RATE_APPROX: float = 0.0017  # ~0.17%

    # ── Synthetic Enrichment ─────────────────
    MERCHANT_CATEGORIES: list[str] = [
        "Grocery", "Gas Station", "Restaurant", "Online Retail",
        "Travel", "Entertainment", "Healthcare", "Utilities",
        "Department Store", "Electronics",
    ]
    REFERENCE_START_DATE: str = "2023-01-01"  # Synthetic date anchor
    NUM_SYNTHETIC_CUSTOMERS: int = 5000
