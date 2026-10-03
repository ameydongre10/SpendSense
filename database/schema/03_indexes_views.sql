-- ============================================================
-- SpendSense — Indexes & Analytical Views
-- 03_indexes_views.sql
-- ============================================================

SET search_path TO spendsense, public;

-- ── Performance Indexes ──────────────────────

CREATE INDEX IF NOT EXISTS idx_txn_is_fraud
    ON transactions(is_fraud);

CREATE INDEX IF NOT EXISTS idx_txn_amount
    ON transactions(amount);

CREATE INDEX IF NOT EXISTS idx_txn_time
    ON transactions(time_elapsed);

CREATE INDEX IF NOT EXISTS idx_enrich_customer
    ON customer_enrichment(customer_id);

CREATE INDEX IF NOT EXISTS idx_enrich_date
    ON customer_enrichment(transaction_date);

CREATE INDEX IF NOT EXISTS idx_enrich_category
    ON customer_enrichment(merchant_category);

CREATE INDEX IF NOT EXISTS idx_rfm_segment
    ON rfm_segments(segment_label);

CREATE INDEX IF NOT EXISTS idx_cohort_month
    ON cohort_analysis(cohort_month);

CREATE INDEX IF NOT EXISTS idx_anomaly_is_anomaly
    ON billing_anomalies(is_anomaly);

-- ── Analytical Views ─────────────────────────

-- Overview statistics
CREATE OR REPLACE VIEW v_transaction_overview AS
SELECT
    COUNT(*)                                          AS total_transactions,
    SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END)    AS fraud_count,
    SUM(CASE WHEN is_fraud = 0 THEN 1 ELSE 0 END)    AS legitimate_count,
    ROUND(100.0 * SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END)
          / NULLIF(COUNT(*), 0), 4)                   AS fraud_rate_pct,
    ROUND(SUM(amount)::NUMERIC, 2)                    AS total_amount,
    ROUND(SUM(CASE WHEN is_fraud = 1 THEN amount ELSE 0 END)::NUMERIC, 2)
                                                      AS total_fraud_amount,
    ROUND(SUM(CASE WHEN is_fraud = 0 THEN amount ELSE 0 END)::NUMERIC, 2)
                                                      AS total_legitimate_amount,
    ROUND(AVG(amount)::NUMERIC, 2)                    AS avg_transaction_amount,
    ROUND(AVG(CASE WHEN is_fraud = 1 THEN amount END)::NUMERIC, 2)
                                                      AS avg_fraud_amount,
    ROUND(AVG(CASE WHEN is_fraud = 0 THEN amount END)::NUMERIC, 2)
                                                      AS avg_legitimate_amount
FROM transactions;

-- Fraud rate by time period (using synthetic dates)
CREATE OR REPLACE VIEW v_fraud_trend AS
SELECT
    ce.transaction_date,
    DATE_TRUNC('month', ce.transaction_date)::DATE    AS trend_month,
    COUNT(*)                                          AS txn_count,
    SUM(CASE WHEN t.is_fraud = 1 THEN 1 ELSE 0 END)  AS fraud_count,
    ROUND(100.0 * SUM(CASE WHEN t.is_fraud = 1 THEN 1 ELSE 0 END)
          / NULLIF(COUNT(*), 0), 4)                   AS fraud_rate_pct,
    ROUND(SUM(CASE WHEN t.is_fraud = 1 THEN t.amount ELSE 0 END)::NUMERIC, 2)
                                                      AS fraud_amount
FROM transactions t
JOIN customer_enrichment ce ON t.transaction_id = ce.transaction_id
GROUP BY ce.transaction_date, DATE_TRUNC('month', ce.transaction_date)
ORDER BY ce.transaction_date;

-- Spend by merchant category
CREATE OR REPLACE VIEW v_spend_by_category AS
SELECT
    ce.merchant_category,
    COUNT(*)                                          AS txn_count,
    ROUND(SUM(t.amount)::NUMERIC, 2)                  AS total_spend,
    ROUND(AVG(t.amount)::NUMERIC, 2)                  AS avg_spend,
    SUM(CASE WHEN t.is_fraud = 1 THEN 1 ELSE 0 END)  AS fraud_count,
    ROUND(100.0 * SUM(CASE WHEN t.is_fraud = 1 THEN 1 ELSE 0 END)
          / NULLIF(COUNT(*), 0), 4)                   AS fraud_rate_pct
FROM transactions t
JOIN customer_enrichment ce ON t.transaction_id = ce.transaction_id
GROUP BY ce.merchant_category
ORDER BY total_spend DESC;

-- Customer spend summary (for RFM inputs)
CREATE OR REPLACE VIEW v_customer_summary AS
SELECT
    ce.customer_id,
    COUNT(*)                                          AS txn_count,
    ROUND(SUM(t.amount)::NUMERIC, 2)                  AS total_spend,
    ROUND(AVG(t.amount)::NUMERIC, 2)                  AS avg_spend,
    MIN(ce.transaction_date)                          AS first_txn_date,
    MAX(ce.transaction_date)                          AS last_txn_date,
    SUM(CASE WHEN t.is_fraud = 1 THEN 1 ELSE 0 END)  AS fraud_count
FROM transactions t
JOIN customer_enrichment ce ON t.transaction_id = ce.transaction_id
GROUP BY ce.customer_id;

-- Segment profitability summary
CREATE OR REPLACE VIEW v_segment_summary AS
SELECT
    sp.segment_label,
    sp.customer_count,
    sp.total_spend,
    sp.avg_spend,
    sp.avg_frequency,
    sp.fraud_rate,
    sp.profit_index,
    sp.revenue_share
FROM segment_profitability sp
ORDER BY sp.profit_index DESC;
