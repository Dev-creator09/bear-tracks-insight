"""Pydantic schemas for request/response validation."""

from app.schemas.course import (
    CourseBase,
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    CourseSentimentResponse,
)
from app.schemas.health import HealthResponse
from app.schemas.contracts import (
    Course,
    CourseSentiment,
    CourseWithSentiment,
    CourseSearchResult,
    PaginationParams,
    PaginationMeta,
    CourseFilters,
    SearchQuery,
    PrerequisiteNode,
    PrerequisiteRef,
    CourseListResponse,
    CourseDetailResponse,
    CourseSearchResponse,
    PrerequisiteTreeResponse,
    ScrapeJobRequest,
    ScrapeJobResponse,
    HealthStatus,
    ErrorResponse,
    ValidationErrorResponse,
)

__all__ = [
    # Legacy schemas
    "CourseBase",
    "CourseCreate",
    "CourseUpdate",
    "CourseResponse",
    "CourseSentimentResponse",
    "HealthResponse",
    # Contract schemas
    "Course",
    "CourseSentiment",
    "CourseWithSentiment",
    "CourseSearchResult",
    "PaginationParams",
    "PaginationMeta",
    "CourseFilters",
    "SearchQuery",
    "PrerequisiteNode",
    "PrerequisiteRef",
    "CourseListResponse",
    "CourseDetailResponse",
    "CourseSearchResponse",
    "PrerequisiteTreeResponse",
    "ScrapeJobRequest",
    "ScrapeJobResponse",
    "HealthStatus",
    "ErrorResponse",
    "ValidationErrorResponse",
]
