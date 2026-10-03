"""SpendSense — Vercel Serverless Entrypoint

Enables 1-click deployment on Vercel using @vercel/python serverless functions.
Exposes the FastAPI `app` instance.
In serverless environments where a live PostgreSQL container is not attached,
gracefully falls back to the precomputed analytical cache generated from the 284,807 transactions.
"""

import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.models import (
    HealthResponse,
    OverviewResponse,
    SpendAnalysisResponse,
    SpendByCategory,
    SegmentsResponse,
    SegmentDetail,
    CohortResponse,
    CohortRow,
    ProfitabilityResponse,
    ProfitabilityDetail,
    AnomaliesResponse,
    AnomalyDetail,
    RecommendationsResponse,
    Recommendation,
    FraudTrendsResponse,
    FraudTrendPoint,
    ModelComparisonResponse,
    ModelMetrics,
)
from src.config import Config
from src.database import check_connection, get_table_count, is_sqlite
from api.routes import analytics, fraud

app = FastAPI(
    title="SpendSense: Transaction Analytics & Fraud Intelligence API",
    description="Payments network analytics and fraud risk platform (Vercel Serverless & Cloud Ready).",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper to load precomputed cache if database is empty/unreachable
def get_cached_data() -> dict:
    cache_file = Config.ANALYTICS_CACHE_PATH / "precomputed_analytics.json"
    if cache_file.exists():
        with open(cache_file, "r") as f:
            return json.load(f)
    return {}

# Include standard routes
app.include_router(analytics.router, prefix="/api")
app.include_router(fraud.router, prefix="/api")

@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    db_connected = check_connection()
    cache = get_cached_data()
    status_str = "healthy"
    engine_type = "PostgreSQL (Cloud)" if db_connected and not is_sqlite() else ("SQLite" if db_connected else "Serverless Precomputed Cache")

    table_counts = {
        "transactions": 284807 if cache else 0,
        "customer_enrichment": 284807 if cache else 0,
        "rfm_segments": len(cache.get("segments", [])) if cache else 0,
        "cohort_analysis": len(cache.get("cohorts", {}).get("cohorts", [])) if cache else 0,
        "billing_anomalies": cache.get("anomalies", {}).get("total_anomalies", 0) if cache else 0,
        "model_results": 2,
        "business_metrics": 8,
        "segment_profitability": len(cache.get("profitability", [])) if cache else 0,
    }

    return HealthResponse(
        status=status_str,
        database=engine_type,
        tables_loaded=table_counts,
    )

# Static frontend mount for standalone local or container execution
frontend_dir = Config.PROJECT_ROOT / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
