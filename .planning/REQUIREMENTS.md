# SpendSense Requirements Specification (v2.0 Enterprise Overhaul)

## 1. Functional Requirements
- **FR-01 Single Source of Truth Frontend:** Eliminate triple duplication across `frontend/`, `docs/`, and `public/`. Unify into an engineered frontend directory with automated sync/build scripts.
- **FR-02 Swiss Modernist Design System:** Redesign UI using high-density financial data tables, crisp borders, dark graphite slate (`#0B0F17`), cyan-emerald risk status tokens (`#00E599` low risk, `#FFB703` medium, `#FF3366` critical fraud), tabular numerals (`font-variant-numeric: tabular-nums`), and full WCAG AA contrast compliance (minimum 4.5:1 ratio).
- **FR-03 Interactive Simulators:**
  - Real-time Decision Threshold Simulator linking XGBoost Precision-Recall curve to False Positive rate and avoided revenue at risk ($42,538.90).
  - Dynamic Network Take-Rate Simulator (0.5% – 5.0%) dynamically recomputing net portfolio contribution margin.
- **FR-04 Six Analytical Pillars:** Fully interactive telemetry dashboards for Fraud Trajectories, Merchant Mix, RFM Segments, Cohort Decay Matrix, Segment Profitability, and Explainable Billing Anomalies with live search and severity filtering.
- **FR-05 Resilient Dual-Engine Backend:** FastAPI async endpoints serving live database tables or instant cached analytics without cold-start network hangs.
- **FR-06 Executive Deliverables:** Embedded slide deck preview and download capability for the 6-slide executive board presentation (`deliverables/SpendSense_Recommendations.pptx`).

## 2. Security & Compliance Requirements
- **SEC-01 Spec-Compliant CORS:** Eliminate wildcard credentials vulnerability (`allow_origins=["*"]` + `allow_credentials=True`). Support configurable allowed origins.
- **SEC-02 Security Middleware:** Inject Content-Security-Policy (CSP), X-Content-Type-Options, X-Frame-Options, and Referrer-Policy headers.
- **SEC-03 Rate Limiting & Input Sanitization:** Centralized rate limiting middleware and strict query parameter validation.
- **SEC-04 SQLite Relational Integrity:** Enforce `PRAGMA foreign_keys = ON;` on every SQLite connection.

## 3. Performance & Quality Requirements
- **NFR-01 Sub-second API Latency:** All API endpoints respond in < 150ms.
- **NFR-02 Zero Layout Shifts:** Cumulative Layout Shift (CLS) < 0.05.
- **NFR-03 Production Test Coverage:** Complete Pytest test suite covering endpoints, failure modes, models, and calculation engines with 100% test pass rate.
- **NFR-04 CI/CD Pipeline:** Fully configured GitHub Actions workflow (`.github/workflows/ci.yml`) validating linting, testing, and Docker build.
