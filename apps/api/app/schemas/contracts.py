"""
Pydantic models for API contracts
Matches OpenAPI specification and Zod schemas
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field, UUID4, field_validator, ConfigDict


# ============================================================================
# Course Models
# ============================================================================

class CourseBase(BaseModel):
    """Base course fields"""

    subject: str = Field(..., min_length=2, max_length=10, description="Course subject code")
    number: int = Field(..., ge=100, le=999, description="Course number")
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    credits: float = Field(..., gt=0)
    faculty: str = Field(..., min_length=1, max_length=100)
    prerequisite_codes: List[str] = Field(default_factory=list, alias="prerequisiteCodes")
    term_availability: List[str] = Field(default_factory=list, alias="termAvailability")


class Course(CourseBase):
    """Full course model with ID and timestamps"""

    id: UUID4
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class CourseSentiment(BaseModel):
    """Course sentiment and metrics"""

    id: UUID4
    course_id: UUID4 = Field(alias="courseId")
    reddit_thread_ids: List[str] = Field(default_factory=list, alias="redditThreadIds")
    difficulty_avg: Optional[float] = Field(None, ge=1, le=5, alias="difficultyAvg")
    workload_avg: Optional[float] = Field(None, ge=0, le=40, alias="workloadAvg")
    gpa_estimate: Optional[float] = Field(None, ge=0, le=4, alias="gpaEstimate")
    professor_mentions: Optional[Dict[str, float]] = Field(None, alias="professorMentions")
    warnings: List[str] = Field(default_factory=list)
    last_scraped_at: datetime = Field(alias="lastScrapedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class CourseWithSentiment(Course):
    """Course with optional sentiment data"""

    sentiment: Optional[CourseSentiment] = None


class CourseSearchResult(CourseWithSentiment):
    """Course search result with relevance score"""

    relevance_score: float = Field(..., ge=0, le=1, alias="relevanceScore")
    reasoning: Optional[str] = None


# ============================================================================
# Pagination Models
# ============================================================================

class PaginationParams(BaseModel):
    """Pagination query parameters"""

    cursor: Optional[str] = None
    limit: int = Field(50, ge=1, le=100)


class PaginationMeta(BaseModel):
    """Pagination metadata"""

    cursor: Optional[str] = None
    next_cursor: Optional[str] = Field(None, alias="nextCursor")
    limit: int
    has_more: bool = Field(alias="hasMore")

    model_config = ConfigDict(populate_by_name=True)


# ============================================================================
# Filter Models
# ============================================================================

class CourseFilters(BaseModel):
    """Course filtering parameters"""

    faculty: Optional[str] = None
    subject: Optional[str] = None
    min_gpa: Optional[float] = Field(None, ge=0, le=4, alias="minGpa")
    max_difficulty: Optional[float] = Field(None, ge=1, le=5, alias="maxDifficulty")
    term: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


# ============================================================================
# Search Models
# ============================================================================

class SearchQuery(BaseModel):
    """Semantic search query"""

    query: str = Field(..., min_length=1, max_length=500)
    filters: Optional[CourseFilters] = None
    limit: int = Field(10, ge=1, le=50)


# ============================================================================
# Prerequisite Models
# ============================================================================

class PrerequisiteNode(BaseModel):
    """Recursive prerequisite tree node"""

    course: Course
    children: List['PrerequisiteNode'] = Field(default_factory=list)


# Enable forward references for recursive model
PrerequisiteNode.model_rebuild()


class PrerequisiteRef(BaseModel):
    """Simple prerequisite reference"""

    id: UUID4
    course: Course


# ============================================================================
# Response Models
# ============================================================================

class CourseListResponse(BaseModel):
    """Paginated course list response"""

    courses: List[CourseWithSentiment]
    pagination: PaginationMeta


class CourseDetailResponse(CourseWithSentiment):
    """Detailed course response with prerequisites"""

    prerequisites: List[PrerequisiteRef] = Field(default_factory=list)
    required_by: List[PrerequisiteRef] = Field(default_factory=list, alias="requiredBy")

    model_config = ConfigDict(populate_by_name=True)


class CourseSearchResponse(BaseModel):
    """Search response with results and metadata"""

    results: List[CourseSearchResult]
    query: str
    total_results: int = Field(alias="totalResults")
    filters_applied: Optional[Dict[str, Any]] = Field(
        default_factory=dict, alias="filtersApplied"
    )
    cost_usd: Optional[float] = Field(None, alias="costUsd")
    latency_ms: Optional[int] = Field(None, alias="latencyMs")

    model_config = ConfigDict(populate_by_name=True)


class PrerequisiteTreeResponse(BaseModel):
    """Prerequisite tree response"""

    course: Course
    tree: PrerequisiteNode
    depth: int


# ============================================================================
# Scrape Models
# ============================================================================

class ScrapeStatus(str, Enum):
    """Scrape job status"""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ScrapeJobRequest(BaseModel):
    """Request to trigger scrape job"""

    subject: str = Field(..., min_length=2, max_length=10)
    number: int = Field(..., ge=100, le=999)
    term: str = Field(..., min_length=1, max_length=50)
    force: bool = False


class ScrapeJobResponse(BaseModel):
    """Scrape job response"""

    job_id: UUID4 = Field(alias="jobId")
    status: ScrapeStatus
    message: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


# ============================================================================
# Health Models
# ============================================================================

class HealthStatus(str, Enum):
    """Health status"""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class HealthResponse(BaseModel):
    """Health check response"""

    status: HealthStatus
    database: str
    redis: str
    version: Optional[str] = None
    uptime_seconds: Optional[float] = Field(None, alias="uptimeSeconds")
    timestamp: Optional[datetime] = None

    model_config = ConfigDict(populate_by_name=True)


# ============================================================================
# Error Models
# ============================================================================

class ErrorResponse(BaseModel):
    """Generic error response"""

    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    path: Optional[str] = None
    timestamp: Optional[datetime] = None


class ValidationErrorDetail(BaseModel):
    """Validation error detail"""

    field: str
    message: str
    code: Optional[str] = None


class ValidationErrorResponse(ErrorResponse):
    """Validation error response"""

    code: str = "VALIDATION_ERROR"
    errors: List[ValidationErrorDetail] = Field(default_factory=list)
