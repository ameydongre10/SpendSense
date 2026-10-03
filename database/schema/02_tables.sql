-- ============================================================
-- SpendSense — Table Definitions
-- 02_tables.sql
-- ============================================================
-- Core tables for the SpendSense analytical database.
--
-- DATA LINEAGE:
--   transactions        ← Kaggle Credit Card Fraud Detection dataset
--                         (Time, V1-V28, Amount, Class)
--   customer_enrichment ← SYNTHETIC data generated to support RFM,
--                         cohort, and profitability analysis.
--                         Clearly labeled as synthetic.
--   rfm_segments        ← Computed by analytics pipeline
--   cohort_analysis     ← Computed by analytics pipeline
--   billing_anomalies   ← Computed by analytics pipeline
--   model_results       ← Computed by ML pipeline
--   business_metrics    ← Computed by metrics pipeline
-- ============================================================

SET search_path TO spendsense, public;

-- ────────────────────────────────────────────
-- RAW TRANSACTION DATA (from Kaggle dataset)
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id    SERIAL PRIMARY KEY,
    time_elapsed      DOUBLE PRECISION NOT NULL,  -- seconds from first txn
    v1  DOUBLE PRECISION, v2  DOUBLE PRECISION, v3  DOUBLE PRECISION,
    v4  DOUBLE PRECISION, v5  DOUBLE PRECISION, v6  DOUBLE PRECISION,
    v7  DOUBLE PRECISION, v8  DOUBLE PRECISION, v9  DOUBLE PRECISION,
    v10 DOUBLE PRECISION, v11 DOUBLE PRECISION, v12 DOUBLE PRECISION,
    v13 DOUBLE PRECISION, v14 DOUBLE PRECISION, v15 DOUBLE PRECISION,
    v16 DOUBLE PRECISION, v17 DOUBLE PRECISION, v18 DOUBLE PRECISION,
    v19 DOUBLE PRECISION, v20 DOUBLE PRECISION, v21 DOUBLE PRECISION,
    v22 DOUBLE PRECISION, v23 DOUBLE PRECISION, v24 DOUBLE PRECISION,
    v25 DOUBLE PRECISION, v26 DOUBLE PRECISION, v27 DOUBLE PRECISION,
    v28 DOUBLE PRECISION,
    amount            DOUBLE PRECISION NOT NULL CHECK (amount >= 0),
    is_fraud          SMALLINT NOT NULL CHECK (is_fraud IN (0, 1)),
    created_at        TIMESTAMP DEFAULT NOW()
);

-- ────────────────────────────────────────────
-- SYNTHETIC CUSTOMER ENRICHMENT
-- ────────────────────────────────────────────
-- NOTE: This table contains SYNTHETIC data generated to enable
-- RFM segmentation, cohort analysis, and profitability analysis.
-- It is NOT from the original Kaggle dataset.
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS customer_enrichment (
    transaction_id    INTEGER PRIMARY KEY REFERENCES transactions(transaction_id),
    customer_id       VARCHAR(20) NOT NULL,
    transaction_date  DATE NOT NULL,
    merchant_category VARCHAR(50) NOT NULL,
    city              VARCHAR(100),
    state             VARCHAR(50),
    is_synthetic      BOOLEAN DEFAULT TRUE  -- always TRUE, transparency marker
);

-- ────────────────────────────────────────────
-- RFM SEGMENTS (computed by analytics)
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS rfm_segments (
    customer_id       VARCHAR(20) PRIMARY KEY,
    recency_days      INTEGER NOT NULL,
    frequency         INTEGER NOT NULL,
    monetary          DOUBLE PRECISION NOT NULL,
    r_score           SMALLINT NOT NULL CHECK (r_score BETWEEN 1 AND 5),
    f_score           SMALLINT NOT NULL CHECK (f_score BETWEEN 1 AND 5),
    m_score           SMALLINT NOT NULL CHECK (m_score BETWEEN 1 AND 5),
    rfm_score         SMALLINT NOT NULL,       -- r_score + f_score + m_score
    segment_label     VARCHAR(30) NOT NULL,
    computed_at       TIMESTAMP DEFAULT NOW()
);

-- ────────────────────────────────────────────
-- COHORT ANALYSIS (computed by analytics)
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS cohort_analysis (
    cohort_id         SERIAL PRIMARY KEY,
    cohort_month      DATE NOT NULL,           -- first transaction month
    period_month      DATE NOT NULL,           -- observation month
    period_index      INTEGER NOT NULL,        -- months since cohort start
    customer_count    INTEGER NOT NULL,
    retention_rate    DOUBLE PRECISION,
    total_spend       DOUBLE PRECISION,
    avg_spend         DOUBLE PRECISION,
    computed_at       TIMESTAMP DEFAULT NOW(),
    UNIQUE (cohort_month, period_month)
);

-- ────────────────────────────────────────────
-- BILLING ANOMALIES (computed by analytics)
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS billing_anomalies (
    anomaly_id        SERIAL PRIMARY KEY,
    transaction_id    INTEGER REFERENCES transactions(transaction_id),
    customer_id       VARCHAR(20),
    amount            DOUBLE PRECISION NOT NULL,
    anomaly_score     DOUBLE PRECISION NOT NULL,
    is_anomaly        BOOLEAN NOT NULL,
    detection_method  VARCHAR(50) NOT NULL,    -- 'zscore', 'iqr', 'isolation_forest'
    reason            TEXT,
    detected_at       TIMESTAMP DEFAULT NOW()
);

-- ────────────────────────────────────────────
-- MODEL RESULTS (computed by ML pipeline)
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS model_results (
    model_id          SERIAL PRIMARY KEY,
    model_name        VARCHAR(50) NOT NULL,     -- 'logistic_regression', 'xgboost'
    precision_score   DOUBLE PRECISION NOT NULL,
    recall_score      DOUBLE PRECISION NOT NULL,
    f1_score          DOUBLE PRECISION NOT NULL,
    auprc             DOUBLE PRECISION NOT NULL,
    roc_auc           DOUBLE PRECISION,
    threshold         DOUBLE PRECISION,
    true_positives    INTEGER,
    false_positives   INTEGER,
    true_negatives    INTEGER,
    false_negatives   INTEGER,
    class_imbalance_strategy VARCHAR(50),       -- 'smote', 'class_weight', etc.
    training_samples  INTEGER,
    test_samples      INTEGER,
    trained_at        TIMESTAMP DEFAULT NOW(),
    notes             TEXT
);

-- ────────────────────────────────────────────
-- PRECOMPUTED BUSINESS METRICS
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS business_metrics (
    metric_id         SERIAL PRIMARY KEY,
    metric_name       VARCHAR(80) NOT NULL UNIQUE,
    metric_value      DOUBLE PRECISION NOT NULL,
    metric_unit       VARCHAR(30),              -- 'percent', 'dollars', 'count'
    formula           TEXT,
    data_source       TEXT,
    computed_at       TIMESTAMP DEFAULT NOW()
);

-- ────────────────────────────────────────────
-- SEGMENT PROFITABILITY (computed by analytics)
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS segment_profitability (
    segment_label     VARCHAR(30) PRIMARY KEY,
    customer_count    INTEGER NOT NULL,
    total_spend       DOUBLE PRECISION NOT NULL,
    avg_spend         DOUBLE PRECISION NOT NULL,
    avg_frequency     DOUBLE PRECISION NOT NULL,
    fraud_rate        DOUBLE PRECISION,
    profit_index      DOUBLE PRECISION NOT NULL, -- relative profitability
    revenue_share     DOUBLE PRECISION,          -- % of total revenue
    computed_at       TIMESTAMP DEFAULT NOW()
);
