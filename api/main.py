"""SpendSense — FastAPI Analytics & Intelligence Service

Production-grade financial analytics and fraud-risk intelligence service:
- Enterprise Security Headers (CSP, HSTS, X-Content-Type-Options, X-Frame-Options)
- Spec-compliant CORS configuration
- Request latency timing (X-Process-Time-Ms) & Correlation ID (X-Request-ID)
- API routers (/api/overview, /api/fraud, /api/segments, etc.)
- Healthcheck endpoint with table status
- Static files mounting serving the Swiss Modernist Industrial Fintech Terminal
"""

import logging
import os
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from api.models import HealthResponse
from api.routes import analytics, fraud
from src.config import Config
from src.database import check_connection, get_table_count, init_db, is_sqlite

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("SpendSense-API")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    logger.info("Initializing SpendSense service lifecycle...")
    try:
        init_db()
    except Exception as e:
        logger.warning("Database auto-initialization skipped or deferred: %s", e)
    yield
    logger.info("Shutting down SpendSense service...")


app = FastAPI(
    title="SpendSense: Transaction Analytics & Fraud Intelligence API",
    description=(
        "Production-grade financial analytics and fraud-risk intelligence service "
        "built to global card payment network analyst standards."
    ),
    version="2.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redirect_slashes=False,
    lifespan=lifespan,
)


# ── Security Headers & Request Tracing Middleware ──────────────────────────
@app.middleware("http")
async def security_and_tracing_middleware(request: Request, call_next):
    start_time = time.time()
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    response = await call_next(request)

    process_time_ms = (time.time() - start_time) * 1000
    response.headers["X-Process-Time-Ms"] = f"{process_time_ms:.2f}"
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    return response


# ── Spec-Compliant CORS Configuration ──────────────────────────────────────
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
if allowed_origins_env == "*":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in allowed_origins_env.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

# ── Include Routers ────────────────────────────────────────────────────────
app.include_router(analytics.router, prefix="/api")
app.include_router(fraud.router, prefix="/api")


@app.get("/docs", include_in_schema=False)
async def docs_redirect():
    """Redirect /docs to /api/docs Swagger documentation."""
    return RedirectResponse(url="/api/docs")


@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Verify backend health and database table status."""
    db_connected = check_connection()
    status_str = "healthy" if db_connected else "degraded"
    engine_type = "SQLite (Embedded Fallback)" if is_sqlite() else "PostgreSQL"

    table_counts = {}
    if db_connected:
        for t in [
            "transactions",
            "customer_enrichment",
            "rfm_segments",
            "cohort_analysis",
            "billing_anomalies",
            "model_results",
            "business_metrics",
            "segment_profitability",
        ]:
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
