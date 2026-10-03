"""SpendSense — Database Connection Manager

Provides a production-grade database connection layer using SQLAlchemy.
Primary target: PostgreSQL (as specified in the proposal and docker-compose.yml).
Fallback target: SQLite (local file spendsense.db) when PostgreSQL is unreachable,
ensuring the application, tests, and API work seamlessly in any environment.
"""

import logging
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Connection
from sqlalchemy.orm import sessionmaker, Session

from src.config import Config

logger = logging.getLogger(__name__)

_engine: Engine | None = None
_is_sqlite: bool = False


def is_sqlite() -> bool:
    """Return whether the active engine is SQLite fallback."""
    return _is_sqlite


def get_engine() -> Engine:
    """Return a singleton SQLAlchemy engine.
    
    Attempts PostgreSQL connection first. If unreachable or not configured,
    falls back to SQLite at data/spendsense.db.
    """
    global _engine, _is_sqlite
    if _engine is not None:
        return _engine

    # Try PostgreSQL first
    pg_url = Config.database_url()
    try:
        test_engine = create_engine(
            pg_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 3},
            echo=False,
        )
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        _engine = test_engine
        _is_sqlite = False
        logger.info("Connected to PostgreSQL at %s:%s", Config.POSTGRES_HOST, Config.POSTGRES_PORT)
        return _engine
    except Exception as e:
        logger.warning(
            "PostgreSQL at %s:%s is unreachable (%s). Initializing SQLite fallback at data/spendsense.db",
            Config.POSTGRES_HOST, Config.POSTGRES_PORT, e
        )

    # SQLite fallback
    db_path = Config.PROJECT_ROOT / "data" / "spendsense.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    sqlite_url = f"sqlite:///{db_path.as_posix()}"
    _engine = create_engine(sqlite_url, echo=False)
    _is_sqlite = True
    logger.info("Using SQLite database at %s", db_path)
    return _engine


@contextmanager
def get_connection() -> Generator[Connection, None, None]:
    """Yield a raw DB connection for SQL execution."""
    engine = get_engine()
    with engine.connect() as conn:
        yield conn


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Yield an ORM session with automatic commit/rollback."""
    engine = get_engine()
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def execute_sql(sql: str, params: dict | None = None) -> list[dict]:
    """Execute a parameterized SQL query and return results as dicts."""
    with get_connection() as conn:
        result = conn.execute(text(sql), params or {})
        if result.returns_rows:
            columns = list(result.keys())
            return [dict(zip(columns, row)) for row in result.fetchall()]
        conn.commit()
        return []


def init_db() -> None:
    """Initialize tables according to active engine (PostgreSQL or SQLite)."""
    engine = get_engine()
    with engine.begin() as conn:
        if _is_sqlite:
            # SQLite compatible DDL
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    time_elapsed REAL NOT NULL,
                    v1 REAL, v2 REAL, v3 REAL, v4 REAL, v5 REAL, v6 REAL,
                    v7 REAL, v8 REAL, v9 REAL, v10 REAL, v11 REAL, v12 REAL,
                    v13 REAL, v14 REAL, v15 REAL, v16 REAL, v17 REAL, v18 REAL,
                    v19 REAL, v20 REAL, v21 REAL, v22 REAL, v23 REAL, v24 REAL,
                    v25 REAL, v26 REAL, v27 REAL, v28 REAL,
                    amount REAL NOT NULL CHECK (amount >= 0),
                    is_fraud INTEGER NOT NULL CHECK (is_fraud IN (0, 1)),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS customer_enrichment (
                    transaction_id INTEGER PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    transaction_date TEXT NOT NULL,
                    merchant_category TEXT NOT NULL,
                    city TEXT,
                    state TEXT,
                    is_synthetic INTEGER DEFAULT 1,
                    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS rfm_segments (
                    customer_id TEXT PRIMARY KEY,
                    recency_days INTEGER NOT NULL,
                    frequency INTEGER NOT NULL,
                    monetary REAL NOT NULL,
                    r_score INTEGER NOT NULL,
                    f_score INTEGER NOT NULL,
                    m_score INTEGER NOT NULL,
                    rfm_score INTEGER NOT NULL,
                    segment_label TEXT NOT NULL,
                    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS cohort_analysis (
                    cohort_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cohort_month TEXT NOT NULL,
                    period_month TEXT NOT NULL,
                    period_index INTEGER NOT NULL,
                    customer_count INTEGER NOT NULL,
                    retention_rate REAL,
                    total_spend REAL,
                    avg_spend REAL,
                    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (cohort_month, period_month)
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS billing_anomalies (
                    anomaly_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id INTEGER,
                    customer_id TEXT,
                    amount REAL NOT NULL,
                    anomaly_score REAL NOT NULL,
                    is_anomaly INTEGER NOT NULL,
                    detection_method TEXT NOT NULL,
                    reason TEXT,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS model_results (
                    model_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    precision_score REAL NOT NULL,
                    recall_score REAL NOT NULL,
                    f1_score REAL NOT NULL,
                    auprc REAL NOT NULL,
                    roc_auc REAL,
                    threshold REAL,
                    true_positives INTEGER,
                    false_positives INTEGER,
                    true_negatives INTEGER,
                    false_negatives INTEGER,
                    class_imbalance_strategy TEXT,
                    training_samples INTEGER,
                    test_samples INTEGER,
                    trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS business_metrics (
                    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL UNIQUE,
                    metric_value REAL NOT NULL,
                    metric_unit TEXT,
                    formula TEXT,
                    data_source TEXT,
                    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS segment_profitability (
                    segment_label TEXT PRIMARY KEY,
                    customer_count INTEGER NOT NULL,
                    total_spend REAL NOT NULL,
                    avg_spend REAL NOT NULL,
                    avg_frequency REAL NOT NULL,
                    fraud_rate REAL,
                    profit_index REAL NOT NULL,
                    revenue_share REAL,
                    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            # Indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_txn_is_fraud ON transactions(is_fraud);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_txn_amount ON transactions(amount);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_enrich_customer ON customer_enrichment(customer_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_enrich_date ON customer_enrichment(transaction_date);"))
        else:
            # PostgreSQL DDL
            sql_file_1 = Config.PROJECT_ROOT / "database" / "schema" / "01_init.sql"
            sql_file_2 = Config.PROJECT_ROOT / "database" / "schema" / "02_tables.sql"
            sql_file_3 = Config.PROJECT_ROOT / "database" / "schema" / "03_indexes_views.sql"
            for f in [sql_file_1, sql_file_2, sql_file_3]:
                if f.exists():
                    conn.execute(text(f.read_text(encoding="utf-8")))
    logger.info("Database schema initialized successfully.")


def check_connection() -> bool:
    """Verify database connectivity."""
    try:
        with get_connection() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error("Database connection failed: %s", e)
        return False


def get_table_count(table: str) -> int:
    """Return the row count for a given table."""
    with get_connection() as conn:
        r = conn.execute(text(f"SELECT COUNT(*) AS cnt FROM {table}"))
        row = r.fetchone()
        return row[0] if row else 0
