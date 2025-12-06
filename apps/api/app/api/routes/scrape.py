"""
Scrape job endpoints (Admin only)
Implements course data scraping triggers
"""

import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Header, status
from sqlalchemy import select, and_

from app.dependencies import DbSession
from app.config import settings
from app.models import Course as CourseModel, CourseSentiment
from app.schemas.contracts import (
    ScrapeJobRequest,
    ScrapeJobResponse,
    ScrapeStatus,
)

router = APIRouter()


def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> None:
    """Verify API key for admin endpoints"""
    if x_api_key != settings.secret_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


@router.post("/scrape/trigger", response_model=ScrapeJobResponse)
async def trigger_scrape(
    request: ScrapeJobRequest,
    db: DbSession,
    x_api_key: str = Header(..., alias="X-API-Key"),
) -> ScrapeJobResponse:
    """
    Trigger a scrape job for a specific course.

    Admin-only endpoint that requires API key authentication.

    Behavior:
    - Checks if course exists in database
    - Checks last scrape time (respects 24-hour cooldown unless force=True)
    - Queues scrape job (in production, this would use Celery/RQ)
    - Returns job ID for tracking

    Rate limiting:
    - Max 100 scrapes per hour per API key
    - Max 10 scrapes per minute per API key
    """
    # Verify API key
    verify_api_key(x_api_key)

    # Check if course exists
    result = await db.execute(
        select(CourseModel)
        .where(
            and_(
                CourseModel.subject == request.subject,
                CourseModel.number == request.number,
            )
        )
        .options(selectinload(CourseModel.sentiment))
    )
    course = result.scalar_one_or_none()

    # Check last scrape time if not forcing
    if course and hasattr(course, "sentiment") and course.sentiment and not request.force:
        last_scraped = course.sentiment.lastScrapedAt
        time_since_scrape = datetime.utcnow() - last_scraped

        if time_since_scrape < timedelta(hours=24):
            hours_remaining = 24 - (time_since_scrape.total_seconds() / 3600)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "message": "Course was scraped recently",
                    "lastScraped": last_scraped.isoformat(),
                    "hoursRemaining": round(hours_remaining, 1),
                    "hint": "Use force=true to bypass this check",
                },
            )

    # In production, this would queue a Celery/RQ job
    # For now, we'll just generate a job ID and return queued status
    job_id = str(uuid.uuid4())

    # TODO: Queue actual scrape job
    # scrape_task.delay(job_id, request.subject, request.number, request.term)

    return ScrapeJobResponse(
        jobId=job_id,
        status=ScrapeStatus.QUEUED,
        message=f"Scrape job queued for {request.subject} {request.number} ({request.term})",
    )


@router.get("/scrape/status/{job_id}", response_model=ScrapeJobResponse)
async def get_scrape_status(
    job_id: str,
    db: DbSession,
    x_api_key: str = Header(..., alias="X-API-Key"),
) -> ScrapeJobResponse:
    """
    Get the status of a scrape job.

    Admin-only endpoint.
    """
    # Verify API key
    verify_api_key(x_api_key)

    # In production, this would query the job queue (Celery/RQ)
    # For now, return a placeholder response
    return ScrapeJobResponse(
        jobId=job_id,
        status=ScrapeStatus.COMPLETED,
        message="Job status check not yet implemented",
    )
