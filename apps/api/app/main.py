"""FastAPI application entry point with comprehensive API contracts."""

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.api.routes import health
from app.api.routes import courses_v1, search, prerequisites, scrape, evals
from app.database import engine
from app.models import Base
from app.schemas.contracts import ErrorResponse, ValidationErrorResponse, ValidationErrorDetail


# Track start time for uptime calculation
START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup: Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Shutdown: Cleanup
    await engine.dispose()


# Create FastAPI app with OpenAPI configuration
app = FastAPI(
    title="Bear Tracks Course Insight Platform API",
    description="""
    API for discovering courses, analyzing sentiment, and exploring prerequisites
    at University of Alberta.

    ## Features
    - **Course Discovery**: Advanced filtering and pagination
    - **Sentiment Analysis**: Difficulty, workload, and GPA estimates
    - **Semantic Search**: AI-powered course search
    - **Prerequisite Trees**: Recursive dependency graphs
    - **Data Scraping**: Admin endpoints for data collection

    ## Authentication
    Admin endpoints require API key authentication via `X-API-Key` header.

    ## Rate Limiting
    - Public endpoints: 100 requests/minute
    - Search endpoints: 20 requests/minute
    - Admin endpoints: 10 requests/minute
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ============================================================================
# Middleware
# ============================================================================

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "http://localhost:3001",  # Alternative local port
        "https://beartracks.example.com",  # Production (update as needed)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time"],
)


@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    """Add unique request ID to all requests for tracing."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # Process request and measure response time
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    # Add headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{process_time:.3f}s"

    return response


@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    """Log all requests for monitoring."""
    request_id = getattr(request.state, "request_id", "unknown")

    # Log request
    print(f"[{request_id}] {request.method} {request.url.path}")

    # Process request
    response = await call_next(request)

    # Log response
    print(f"[{request_id}] Status: {response.status_code}")

    return response


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with detailed error messages."""
    errors = []

    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append(
            ValidationErrorDetail(
                field=field_path,
                message=error["msg"],
                code=error["type"],
            )
        )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ValidationErrorResponse(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            errors=errors,
            path=request.url.path,
        ).model_dump(by_alias=True),
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ErrorResponse(
            code="NOT_FOUND",
            message="Resource not found",
            path=request.url.path,
        ).model_dump(by_alias=True),
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle internal server errors."""
    request_id = getattr(request.state, "request_id", "unknown")

    print(f"[{request_id}] Internal error: {exc}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            code="INTERNAL_SERVER_ERROR",
            message="An internal server error occurred",
            path=request.url.path,
            details={"request_id": request_id},
        ).model_dump(by_alias=True),
    )


# ============================================================================
# Routers
# ============================================================================

# Health check (no prefix)
app.include_router(health.router, tags=["Health"])

# V1 API routes
app.include_router(courses_v1.router, prefix="/api/v1", tags=["Courses"])
app.include_router(search.router, prefix="/api/v1", tags=["Search"])
app.include_router(prerequisites.router, prefix="/api/v1", tags=["Prerequisites"])
app.include_router(scrape.router, prefix="/api/v1", tags=["Scrape"])
app.include_router(evals.router, prefix="/api/v1/evals", tags=["Evaluations"])


# ============================================================================
# Root Endpoints
# ============================================================================

@app.get("/")
async def root() -> dict:
    """API root endpoint with links to documentation."""
    return {
        "message": "Bear Tracks Course Insight Platform API",
        "version": "1.0.0",
        "uptime_seconds": time.time() - START_TIME,
        "links": {
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
            "health": "/api/v1/health",
        },
    }


@app.get("/api")
async def api_root() -> dict:
    """API version information."""
    return {
        "version": "1.0.0",
        "available_versions": ["v1"],
        "default_version": "v1",
    }


@app.get("/api/v1")
async def api_v1_info() -> dict:
    """API v1 information and available endpoints."""
    return {
        "version": "v1",
        "endpoints": {
            "courses": "/api/v1/courses",
            "search": "/api/v1/courses/search",
            "prerequisites": "/api/v1/prerequisites/{subject}/{number}",
            "scrape": "/api/v1/scrape/trigger",
            "health": "/api/v1/health",
        },
    }
