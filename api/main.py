"""SpendSense — FastAPI Analytics & Intelligence Service

Main application entrypoint configuring:
- CORS middleware for local frontend access
- API routers (/api/overview, /api/fraud, /api/segments, etc.)
- Healthcheck endpoint with database table row counts
- Static files mounting to serve the custom editorial dashboard directly
"""

import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.models import HealthResponse
from api.routes import analytics, fraud
from src.database import check_connection, get_table_count, is_sqlite, init_db
from src.config import Config

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("SpendSense-API")

app = FastAPI(
    title="SpendSense: Transaction Analytics & Fraud Intelligence API",
    description=(
        "Production-grade financial analytics and fraud-risk intelligence service "
        "built to global card payment network analyst standards."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redirect_slashes=False,
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auto-initialize database schema if SQLite fallback is used
try:
    init_db()
except Exception as e:
    logger.warning("Database auto-initialization skipped or deferred: %s", e)

# Include API Routers
app.include_router(analytics.router, prefix="/api")
app.include_router(fraud.router, prefix="/api")


@app.get("/docs", include_in_schema=False)
def docs_redirect():
    """Redirect /docs to /api/docs Swagger documentation."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/docs")


@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Verify backend health and database table status."""
    db_connected = check_connection()
    status_str = "healthy" if db_connected else "degraded"
    engine_type = "SQLite (Embedded Fallback)" if is_sqlite() else "PostgreSQL"

    table_counts = {}
    if db_connected:
        for t in ["transactions", "customer_enrichment", "rfm_segments", "cohort_analysis", "billing_anomalies", "model_results", "business_metrics", "segment_profitability"]:
            try:
                table_counts[t] = get_table_count(t)
            except Exception:
                table_counts[t] = 0

    return HealthResponse(
        status=status_str,
        database=engine_type if db_connected else "unreachable",
        tables_loaded=table_counts,
    )


# Mount static frontend directory
frontend_dir = Config.PROJECT_ROOT / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
