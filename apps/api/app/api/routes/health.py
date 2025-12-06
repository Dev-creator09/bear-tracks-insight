"""Health check endpoints."""

from fastapi import APIRouter, HTTPException
from sqlalchemy import text
import redis.asyncio as redis

from app.config import settings
from app.dependencies import DbSession
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: DbSession) -> HealthResponse:
    """
    Health check endpoint.

    Checks the status of:
    - API service
    - Database connection
    - Redis connection
    """
    # Check database
    db_status = "unhealthy"
    try:
        result = await db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            db_status = "healthy"
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {str(e)}"
        )

    # Check Redis
    redis_status = "unhealthy"
    try:
        redis_client = redis.from_url(settings.redis_url)
        await redis_client.ping()
        redis_status = "healthy"
        await redis_client.aclose()
    except Exception as e:
        # Redis is optional, so we don't raise an exception
        redis_status = f"unhealthy: {str(e)}"

    return HealthResponse(
        status="healthy",
        database=db_status,
        redis=redis_status,
    )
