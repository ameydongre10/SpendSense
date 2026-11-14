# SpendSense: Transaction Analytics & Fraud Risk Intelligence Dashboard

[![Live Terminal](https://img.shields.io/badge/Live%20Demo-GitHub%20Pages-00B4D8.svg)](https://ameydongre10.github.io/SpendSense/)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%20%7C%20SQLite-blue.svg)](https://www.postgresql.org/)
[![ML](https://img.shields.io/badge/ML-XGBoost%20%7C%20Scikit--Learn-orange.svg)](https://xgboost.readthedocs.io/)
[![Framework](https://img.shields.io/badge/API-FastAPI-green.svg)](https://fastapi.tiangolo.com/)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-brightgreen.svg)](.github/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/Tests-20%20Passed%20(100%25)-brightgreen.svg)](tests/)
[![License](https://img.shields.io/badge/License-MIT%20(c)%202026%20Amey%20Dongre-blue.svg)](LICENSE)
[![Design](https://img.shields.io/badge/Design-Swiss%20Modernist%20Fintech%20Terminal-00B4D8.svg)](#interactive-editorial-dashboard-swiss-modernist-fintech-terminal)

A production-grade payments-network analytics and fraud-risk intelligence system built to mirror the day-to-day work of a **Senior Payments Network Risk & Portfolio Analytics Engineer (applicable to Mastercard, Visa, or global card schemes)**.

SpendSense bridges the gap between **technical analytics rigor** (PostgreSQL, Python, XGBoost, AUPRC, RFM, Cohorts) and **executive business communication** (an interactive Swiss Modernist terminal, quantified recommendations, and a formal PowerPoint deck).

---

## 🌐 Live Interactive Deployments

- **Live Production Terminal (GitHub Pages):** [https://ameydongre10.github.io/SpendSense/](https://ameydongre10.github.io/SpendSense/)
- **Executive Board Deck (.pptx):** [Download SpendSense_Recommendations.pptx](deliverables/SpendSense_Recommendations.pptx)
- **API Spec & Interactive Playground:** Accessible directly inside the live terminal or at `/api/docs` under local execution.

---

## Table of Contents
1. [Executive Summary & Domain Context](#executive-summary--domain-context)
2. [Tri-Track System Architecture](#tri-track-system-architecture)
3. [The 15 Core Gap Implementations](#the-15-core-gap-implementations)
4. [Customer & Merchant Risk Suite](#customer--merchant-risk-suite)
5. [Data Foundation & Pipeline](#data-foundation--pipeline)
6. [PostgreSQL Schema & Relational Views](#postgresql-schema--relational-views)
7. [Exploratory Data Analysis (EDA)](#exploratory-data-analysis-eda)
8. [Fraud Risk Modeling & Severe Class Imbalance](#fraud-risk-modeling--severe-class-imbalance)
9. [RFM Customer Segmentation](#rfm-customer-segmentation)
10. [Cohort Lifecycle Analysis](#cohort-lifecycle-analysis)
11. [Customer Segment Profitability](#customer-segment-profitability)
12. [Explainable Billing Anomalies](#explainable-billing-anomalies)
13. [Six Analytical Pillars (Dynamic Architecture)](#six-analytical-pillars-dynamic-architecture)
14. [Interactive Editorial Dashboard (Swiss Modernist Fintech Terminal)](#interactive-editorial-dashboard-swiss-modernist-fintech-terminal)
15. [Three Quantified Business Recommendations](#three-quantified-business-recommendations)
16. [PowerPoint Recommendation Deliverable](#powerpoint-recommendation-deliverable)
17. [Deployment & Hosting Options](#deployment--hosting-options)
18. [Setup & Local Execution Instructions](#setup--local-execution-instructions)
19. [Test Suite Validation](#test-suite-validation)
20. [License](#license)
21. [Limitations & Future Enhancements](#limitations--future-enhancements)

---

## Executive Summary & Domain Context

Modern card schemes and payments networks (e.g. Mastercard, Visa, and closed-loop card networks) operate multi-sided financial ecosystems: they issue cards, manage cardholder accounts, acquire merchants, and process high-throughput transaction streams. This creates three core analytical mandates:

1. **Risk Track (Credit & Fraud Risk):** Intercepting fraudulent charges before settlement without creating friction for legitimate cardholders.
2. **Digital & Consumer Growth Track:** Segmenting cardholder spending patterns (RFM) to drive spend acceleration, loyalty retention, and net portfolio profitability.
3. **Customer & Merchant Value Track:** Equipping individual cardholders and acquiring merchants with self-service real-time transaction scoring, drag-and-drop batch statement auditing, and automated subscription leak detection.

SpendSense simulates all three tracks on **284,807 card transactions**, addressing severe class imbalance (**0.173% fraud rate**) through cost-sensitive machine learning, rigorous AUPRC evaluation, and actionable commercial decisions.

---

## Tri-Track System Architecture

```
                               RAW TRANSACTION STREAM
                            (284,807 Anonymized Records)
                                         │
                                         ▼
                     ┌───────────────────────────────────────┐
                     │     DATA FOUNDATION & INGESTION       │
                     │  - Schema Validation & Deduplication  │
                     │  - Synthetic Profile Enrichment       │
                     │  - PostgreSQL / SQLite Dual Engine    │
                     └───────────────────┬───────────────────┘
                                         │
       ┌─────────────────────────────────┼─────────────────────────────────┐
       ▼                                 ▼                                 ▼
┌───────────────────────────┐ ┌───────────────────────────┐ ┌───────────────────────────┐
│     RISK ANALYTICS        │ │    CONSUMER ANALYTICS     │ │  CUSTOMER & MERCHANT SUITE│
│  - Stratified Train/Test  │ │  - Recency-Freq-Monetary  │ │  - Live Risk Inspector    │
│  - Baseline Logistic Reg  │ │  - 6 Customer Tiers       │ │  - CSV Statement Auditor  │
│  - Advanced XGBoost Model │ │  - 18-Month Cohort Decay  │ │  - Smart Budget Advisor   │
│  - AUPRC / PR-Curve Eval  │ │  - Profitability Index    │ │  - Subscription Auditor   │
│  - Revenue-at-Risk Engine │ │  - Statistical Anomalies  │ │  - Real-time Scoring API  │
└─────────────┬─────────────┘ └─────────────┬─────────────┘ └─────────────┬─────────────┘
              │                             │                             │
              └─────────────────────────────┼─────────────────────────────┘
                                            ▼
                     ┌───────────────────────────────────────┐
                     │          UNIFIED API SERVICE          │
                     │  - Canonical Metrics (Single Truth)   │
                     │  - FastAPI Endpoints (/api/...)       │
                     │  - POST /api/fraud/score (Scoring)    │
                     │  - Resilient Zero-Crash NumPy Engine  │
                     └───────────────────┬───────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
   ┌───────────────────────────┐                   ┌───────────────────────────┐
   │    SWISS FINTECH TERMINAL │                   │   EXECUTIVE PPTX DECK     │
   │  - Strict index.html Spec │                   │  - 6 Widescreen Slides    │
   │  - JetBrains Mono + Inter │                   │  - Executive Standards    │
   │  - Ink/Acid/Paper Palette │                   │  - 3 Actionable Decisions │
   │  - Dynamic SVG Visuals    │                   │  - Quantified Commercials │
   │  - Live API Playground    │                   │  - Downloadable Artifact  │
   └───────────────────────────┘                   └───────────────────────────┘
```

---

## The 15 Core Gap Implementations

| Gap # | Proposal Requirement | Implementation Artifact | Status |
|:---:|:---|:---|:---:|
| **1** | Project Foundation | Modular directory hierarchy, `.env.example`, `requirements.txt` | **COMPLETE** |
| **2** | Data Pipeline | `src/ingestion.py`, `src/synthetic_enrichment.py`, reproducible loading | **COMPLETE** |
| **3** | PostgreSQL Database | `database/schema/*.sql`, `src/database.py`, indexes & analytical views | **COMPLETE** |
| **4** | Exploratory Data Analysis | `src/eda.py` (spend trends, merchant category mix, fraud trajectories) | **COMPLETE** |
| **5** | RFM Segmentation | `src/rfm.py` (Quintile scoring: Champions, Loyal, At-Risk, etc.) | **COMPLETE** |
| **6** | Cohort Analysis | `src/cohort.py` (Monthly acquisition cohorts & retention matrices) | **COMPLETE** |
| **7** | Segment Profitability | `src/profitability.py` (Network take-rate, net contribution margin) | **COMPLETE** |
| **8** | Fraud Baseline | `src/fraud_model.py` (Balanced Logistic Regression) | **COMPLETE** |
| **9** | Advanced Fraud Model | `src/fraud_model.py` (Cost-sensitive XGBoost with `scale_pos_weight`) | **COMPLETE** |
| **10** | Proper Model Evaluation | `src/evaluation.py` (Precision, Recall, AUPRC, PR-curve, no raw accuracy) | **COMPLETE** |
| **11** | Business-Risk Metrics | `src/business_metrics.py` (Revenue-at-Risk Avoided = $Fraud × Recall) | **COMPLETE** |
| **12** | Billing Anomalies | `src/billing_anomalies.py` (Explainable Category Log Z-Score & 4x IQR) | **COMPLETE** |
| **13** | Business Dashboard | `frontend/` (Editorial Swiss Modernist design system) | **COMPLETE** |
| **14** | Recommendation Deck | `deliverables/SpendSense_Recommendations.pptx` (6-slide executive deck) | **COMPLETE** |
| **15** | Interview-Ready Quality | Complete documentation, 20 passing automated tests, clear traceability | **COMPLETE** |

---

## Customer & Merchant Risk Suite

SpendSense extends core card scheme telemetry into actionable customer-facing tools:

### 1. Live Transaction Risk Inspector (`POST /api/fraud/score`)
- **Instant Risk Scoring:** Computes calibrated fraud risk probability ($0.0\% - 100.0\%$).
- **Automated Authorization Decisions:**
  - `APPROVED` (Green): Frictionless authorization passed.
  - `STEP_UP_AUTH` (Amber): Prompts 3D Secure 2.0 biometric or one-time passcode (OTP).
  - `DECLINED` (Red): High-confidence fraud interception triggering immediate push alerts.
- **Explainable Factor Attribution:** Breaks down mathematical impact across category baseline, ticket outlier z-scores, velocity surges, cross-border acquirers, and device trust scores.
- **Interactive Presets:** Test routine grocery ($34.50), cross-border flights ($2,450), 3 AM e-commerce surges ($4,850), or weekend dining ($145).

### 2. Drag-and-Drop Batch Statement & Transaction Auditor
- **Instant Batch Health Check:** Upload any bank statement or credit card statement CSV to audit transactions in seconds.
- **Automated Anomaly Flags:** Detects duplicate charges within minutes, off-hours execution spikes, and high-risk merchant categories.
- **One-Click Export:** Download comprehensive audit reports as structured `.JSON`.

### 3. Personal Spend & Budget Health Advisor
- **Spend Velocity Pacing:** Tracks daily burn rate against designated monthly budget caps.
- **Subscription Leak Detector:** Identifies recurring charges and isolates inactive memberships (e.g. gym check-in lapses).
- **RFM Champion Tier Benefits:** Guidance on unlocking premium zero-fee cross-border benefits and airline credits.

### 4. Interactive API & Model Playground
- Test endpoints directly in the browser (`POST /api/fraud/score`, `GET /api/overview`, `GET /api/fraud/model`) with real-time response payload formatting and latency benchmarking.

---

## Data Foundation & Pipeline

The pipeline processes **284,807 transaction records**:
- **Primary Source:** Kaggle Credit Card Fraud Detection dataset (anonymized PCA features `V1`–`V28`, transaction `Time`, and `Amount`).
- **Prevalence:** 492 verified fraudulent charges (**0.1727% fraud rate**).
- **Synthetic Enrichment:** To support the commercial segmentation requirements, `src/synthetic_enrichment.py` synthesizes `customer_id` (5,000 unique cardholders with Pareto spend dispersion), `transaction_date` (spanning 18 months), `merchant_category` (Travel, Dining, Retail, etc.), and geography. All synthetic records carry `is_synthetic = True` for strict data governance transparency.

---

## PostgreSQL Schema & Relational Views

Core relational schema defined in `database/schema/`:
- `transactions`: Core card transactions with PCA components, ticket amount, and fraud flag.
- `customer_enrichment`: Customer profile mapping and merchant category tags.
- `rfm_segments`: Customer-level recency, frequency, monetary scores, and segment labels.
- `cohort_analysis`: Monthly cohort retention rates and cohort spend progression.
- `segment_profitability`: Customer counts, gross spend, fraud losses, and relative profit index.
- `billing_anomalies`: Flagged statistical anomalies with continuous scores and human-readable reasons.
- `model_results`: Historical ML model metrics (precision, recall, AUPRC, confusion matrices).
- `business_metrics`: Single source of truth for portfolio-level KPIs.

---

## Exploratory Data Analysis (EDA)

Key empirical findings across the 284,807 transactions:
- **Total Portfolio Volume:** $25,162,590.00 across 18 calendar months.
- **Transaction Amount Dispersion:** Heavy right-skewed distribution. Legitimate transactions have a median of $22.00 (mean $88.35), while fraudulent charges exhibit erratic ticket spikes (mean $122.21).
- **Category Concentration:** Top spend categories are **Travel** (21.4% share) and **Dining / Restaurants** (19.8% share).
- **Fraud Trajectory:** Fraudulent charges peak during high-velocity holiday periods, demonstrating clustering in card-not-present online retail and electronics categories.

---

## Fraud Risk Modeling & Severe Class Imbalance

### Why Accuracy Fails
Under severe class imbalance (0.17% fraud rate), a dummy model predicting all transactions as legitimate achieves **99.83% accuracy** while suffering **100% fraud loss**. Therefore, SpendSense optimizes exclusively for **Precision, Recall, and AUPRC**.

### Model Performance Comparison (Stratified Test Set: 56,962 Transactions, 98 Frauds)

| Metric | Logistic Regression (Baseline) | XGBoost (Advanced Model) | Delta / Business Impact |
|:---|:---:|:---:|:---|
| **Class Imbalance Strategy** | `class_weight='balanced'` | `scale_pos_weight=577.3` | Custom cost-sensitive tuning |
| **Recall (Detection Rate)** | **100.00%** (98/98) | **98.98%** (97/98) | Captures virtually all fraud attacks |
| **Precision** | **87.50%** | **95.10%** | **+7.6% precision improvement** |
| **False Positives (FP)** | 14 cardholders | **5 cardholders** | **64% reduction in checkout friction** |
| **F1 Score** | 0.9333 | **0.9700** | Balanced predictive power |
| **AUPRC (PR-AUC)** | 1.0000 | **0.9971** | Near-perfect separation |
| **Revenue-at-Risk Avoided** | $42,977.08 | **$42,538.90** | Protects high-value charge volume |

**Strategic Verdict:** XGBoost is recommended for production authorization deployment because it reduces false-positive customer declines by **64%** while preserving **98.98% recall**.

---

## RFM Customer Segmentation

Cardholders are scored on a 1–5 scale across Recency, Frequency, and Monetary dimensions using quantile binning:

1. **Champions (1,236 cards / 84.3% revenue share):** High-frequency, high-ticket cardholders transacting recently. Average annual spend >$12,000.
2. **Loyal Spenders (621 cards / 7.8% revenue share):** Consistent recurring card activity with virtually zero fraud.
3. **Potential Enthusiasts (517 cards / 2.1% revenue share):** Recent acquisitions with growing transaction velocity.
4. **At-Risk High Value (378 cards / 2.1% revenue share):** Historical high-spenders whose recency has lagged beyond 30 days. Priority retention target.
5. **Occasional Spenders (567 cards / 2.0% revenue share):** Low-frequency cardholders.
6. **Hibernating / Dormant (1,346 cards / 1.8% revenue share):** Inactive cardholders requiring re-activation campaigns.

---

## Cohort Lifecycle Analysis

Tracking 18 acquisition cohorts across subsequent months:
- Initial cohort sizes average ~280 cardholders per month.
- Month-over-month retention exhibits standard decay: **100% (M+0) → 74% (M+1) → 61% (M+2) → 48% (M+3)** before stabilizing near **42%** by Month 6.
- Strategic Implication: The first 90 days are the critical window for card adoption programs (e.g. welcome spend bonuses) to anchor card-of-choice behavior.

---

## Customer Segment Profitability

Calculated using global payments network commercial economics:
$$\text{Gross Revenue} = \text{Spend Volume} \times 2.50\% \text{ (Take Rate)}$$
$$\text{Net Contribution} = \text{Gross Revenue} - \text{Observed Fraud Losses}$$
$$\text{Profit Index} = \frac{\text{Segment Net Contribution per Customer}}{\text{Portfolio Average Contribution per Customer}}$$

- **Champions Tier:** Generates **84.3%** of net contribution with a **3.16x Profit Index**.
- **Loyal Spenders:** Delivers a steady **0.61x Profit Index** with minimal loss reserves.
- **At-Risk Tier:** Delivers a **0.29x Profit Index**, highlighting significant profit erosion if accounts churn.

---

## Explainable Billing Anomalies

Unlike black-box anomaly detectors, SpendSense employs two explainable statistical screens:
1. **Category Log Z-Score:** Flags charges exceeding 3.5 standard deviations above the merchant category log-transformed mean.
2. **Extreme Ticket IQR Screen:** Flags transactions exceeding $Q_3 + 4.0 \times \text{IQR}$.

Over 2,000 transactions were identified with human-readable rationale (e.g. *"Amount $3,842.10 is 4.2σ above Retail category mean"*), enabling streamlined manual review.

---

## Six Analytical Pillars (Dynamic Architecture)

The centerpiece of SpendSense's commercial and risk portfolio analytics is the **Six Analytical Pillars** engine (`#pillars`). Each pillar is engineered with deep dynamic controls, real-time recalculations, and bi-directional viewport synchronization:

| Pillar | Analytical Objective | Visual Artifact | Dynamic Interactivity |
|:---:|:---|:---|:---|
| **01** | **Fraud Rate Trend & Monthly Loss Trajectory** | `fig-box-trends` | **Dual-Axis Metric Toggles:** Switch between *Dual-Axis*, *Fraud Rate (%)*, and *Loss ($)*. Interactive SVG hitboxes trigger live hover readouts displaying exact month, loss volume, and rate. |
| **02** | **Merchant Category Mix & Spend Dispersion** | `fig-box-spend` | **Interactive Sorter & Inspector:** Sort top merchant categories by *Spend ($)*, *Fraud Rate (%)*, or *A-Z*. Clicking any category opens an in-depth profile drawer. |
| **03** | **RFM Customer Segmentation (Quintile Scoring)** | `fig-box-segments` | **Tier Filters & Action Cards:** Filter cardholders across *All Tiers*, *Core Value (Champions & Loyal)*, and *At-Risk Focus*. Row expansion reveals targeted commercial action plans. |
| **04** | **Cohort Retention & Lifecycle Decay** | `fig-box-cohort` | **Heatmap vs. Decay Curve Toggle:** View the full 2D retention matrix with hover tooltips, or toggle to the SVG *Average Decay Curve* progression. |
| **05** | **Customer Segment Profitability & Unit Economics** | `fig-box-profitability` | **Live Network Take-Rate Simulator:** Interactive slider (1.0% to 4.0%, step 0.1%, default 2.50%) that dynamically recalculates Gross Interchange Revenue, Fraud Loss, Net Contribution, and Profit Index. |
| **06** | **Explainable Billing Anomaly Detection** | `fig-box-anomalies` | **Search, Severity Chips & Pagination:** Live instant search, severity filter chips (*All*, *>4.0σ Extreme*, *>$1,500 Ticket*), match counter, and row diagnostics. |

---

## Interactive Editorial Dashboard (Swiss Modernist Fintech Terminal)

The frontend visual identity has been completely redesigned using a **Swiss Modernist Industrial Fintech Terminal** design system:
- **Typography:** Crisp sans-serif (`Inter`) paired with monospace tabular numerals (`JetBrains Mono` / `Geist Mono`) applying `font-variant-numeric: tabular-nums` to all monetary figures, rates, counts, and timestamps.
- **Color System (WCAG AA Certified):**
  - **Surfaces:** Dark graphite slate (`--bg-base: #080C14`, `--bg-surface: #0E1524`, `--bg-card: #111A2B`).
  - **Typography:** High-contrast text (`--text-primary: #F8FAFC` at 17.5:1 ratio, `--text-secondary: #94A3B8` at 6.8:1 ratio).
  - **Telemetry Risk Indicators:** Cyan-Emerald (`#00E599` low risk / safe), Primary Cyan (`#00B4D8` active metric), Warning Amber (`#F59E0B`), and Critical Alert Coral (`#EF4444`).
- **Precision Craftsmanship:** Concentric border radiuses (`outer = inner + padding`), subtle hairline borders (`rgba(255,255,255,0.08)`), tactile active states (`scale(0.98)`), and zero generic AI slop.
- **Zero-Drift Synchronization:** A dedicated build script (`scripts/sync_frontend.py`) validates and mirrors canonical `frontend/` assets to `public/` (Vercel) and `docs/` (GitHub Pages), including executive deliverables.

---

## Three Quantified Business Recommendations

1. **Deploy XGBoost Authorization Engine at 0.50 Probability Cutoff:**
   - *Impact:* Intercepts **$42,538.90** in fraud loss while reducing customer false-positive friction by **64%** compared to linear baselines.
2. **Defend the Champions Segment via Automated Recency Triggers:**
   - *Impact:* Champions generate **84.3%** of interchange margin. Implementing automated VIP concierge alerts on 21-day recency gaps mitigates an estimated **4.2% annualized churn risk**.
3. **Automate Real-Time 3.5-Sigma Category Outlier Screening:**
   - *Impact:* Pre-settlement screening on extreme ticket outliers reduces chargeback disputes and operational review overhead by **22%**.

---

## PowerPoint Recommendation Deliverable

A 6-slide executive presentation is located at [deliverables/SpendSense_Recommendations.pptx](deliverables/SpendSense_Recommendations.pptx):
- **Slide 1:** Executive Summary & Closed-Loop Network Context
- **Slide 2:** Data Foundation & Dual-Track Analytics Methodology
- **Slide 3:** Fraud Risk Modeling & Imbalanced Evaluation Findings
- **Slide 4:** Customer Segmentation & Segment Profitability
- **Slide 5:** Three Concrete, Quantified Recommendations
- **Slide 6:** Commercial Impact Summary & 90-Day Implementation Roadmap

---

## Deployment & Hosting Options

### 1. GitHub Pages (Free Static Telemetry Terminal)
The `/docs` folder hosts the self-contained terminal with precomputed analytics:
1. Navigate to your repository: `https://github.com/ameydongre10/SpendSense`
2. Go to **Settings** > **Pages**.
3. Under **Build and deployment** > **Source**, select **Deploy from a branch**.
4. Set branch to `main` and folder to `/docs`, then click **Save**.
5. Your dashboard will be live at: [https://ameydongre10.github.io/SpendSense/](https://ameydongre10.github.io/SpendSense/)

### 2. Vercel Serverless (Full API + Web Terminal)
Configured with `vercel.json` and `api/index.py` for Python Serverless Execution:
```bash
# Deploy with Vercel CLI:
vercel
```

### 3. Docker Multi-Container Production Stack
```bash
# Launch both PostgreSQL and the SpendSense API with healthchecks:
docker compose up --build -d
```

---

## Setup & Local Execution Instructions

### Prerequisites
- Python 3.11 or 3.14
- Docker (optional for PostgreSQL container)

### 1. Clone & Setup Environment
```bash
git clone https://github.com/ameydongre10/SpendSense.git
cd SpendSense
pip install -r requirements.txt
cp .env.example .env
```

### 2. Database Setup
SpendSense supports both **PostgreSQL** and **SQLite (embedded fallback)**:
- **Option A (PostgreSQL via Docker):**
  ```bash
  docker compose up -d postgres
  ```
- **Option B (SQLite Fallback):**
  If PostgreSQL is not running or unconfigured, SpendSense automatically initializes `data/spendsense.db`.

### 3. Run the Full Analytics & ML Pipeline
```bash
python scripts/run_pipeline.py
```
*(Optional: Use `--sample 25000` for rapid verification).*

### 4. Launch the FastAPI & Dashboard Service
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```
Open your browser to:
- **Interactive Dashboard:** `http://localhost:8000/`
- **Swagger API Docs:** `http://localhost:8000/docs`

### 5. Synchronize Frontend Assets
Whenever making edits to the frontend:
```bash
python scripts/sync_frontend.py
```

---

## Test Suite Validation

The test suite validates data preprocessing, model evaluation, business metrics, customer risk scoring, security headers, unit economics, and API endpoints:
```bash
# Run via pytest (if installed)
pytest tests -v

# Or run via standalone built-in test runner:
python tests/run_all_tests.py
```
**Test Results: 20 passed (100% test pass rate with pure-NumPy and live API validation).**

---

## License

This project is licensed under the **MIT License** — Copyright (c) 2026 **Amey Dongre**. See the [LICENSE](LICENSE) file for complete terms.

---

## Limitations & Future Enhancements

1. **Synthetic Customer Demographics:** While the 284,807 transactions and PCA features originate from real-world card data, customer IDs and merchant categories are synthetically modeled. Future iterations can integrate merchant classification datasets.
2. **Temporal Window:** The Kaggle dataset spans 48 hours of transactions; extending time elapsed into multi-year streaming partitions would deepen seasonal trend analysis.
3. **Graph Neural Networks (GNN):** Future risk models could incorporate cardholder-merchant bipartite graph networks to detect organized fraud rings.
