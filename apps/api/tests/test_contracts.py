"""
Test API contracts and schema validation
Ensures type safety between frontend and backend
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

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
    CourseListResponse,
    CourseDetailResponse,
    CourseSearchResponse,
    PrerequisiteTreeResponse,
    ScrapeJobRequest,
    ScrapeJobResponse,
    HealthResponse,
    HealthStatus,
    ErrorResponse,
    ValidationErrorResponse,
)


# ============================================================================
# Course Schema Tests
# ============================================================================

def test_course_schema_valid():
    """Test valid course creation"""
    course = Course(
        id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        subject="CMPUT",
        number=272,
        title="Formal Systems",
        description="Logic and proofs",
        credits=3.0,
        faculty="Science",
        prerequisiteCodes=["CMPUT 175"],
        termAvailability=["Fall", "Winter"],
        createdAt=datetime.now(),
        updatedAt=datetime.now(),
    )

    assert course.subject == "CMPUT"
    assert course.number == 272
    assert len(course.prerequisiteCodes) == 1


def test_course_schema_invalid_number():
    """Test course with invalid number"""
    with pytest.raises(ValidationError) as exc_info:
        Course(
            id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            subject="CMPUT",
            number=50,  # Invalid: must be >= 100
            title="Test",
            description="Test",
            credits=3.0,
            faculty="Science",
            prerequisiteCodes=[],
            termAvailability=[],
            createdAt=datetime.now(),
            updatedAt=datetime.now(),
        )

    errors = exc_info.value.errors()
    assert any("number" in str(error["loc"]) for error in errors)


def test_course_with_sentiment():
    """Test course with sentiment data"""
    sentiment = CourseSentiment(
        id="b1c2d3e4-f5g6-7890-abcd-ef1234567890",
        courseId="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        redditThreadIds=["abc123"],
        difficultyAvg=3.5,
        workloadAvg=12.0,
        gpaEstimate=3.2,
        professorMentions={"Smith, J.": 4.2},
        warnings=["heavy math"],
        lastScrapedAt=datetime.now(),
    )

    course_with_sent = CourseWithSentiment(
        id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        subject="CMPUT",
        number=272,
        title="Formal Systems",
        description="Logic and proofs",
        credits=3.0,
        faculty="Science",
        prerequisiteCodes=[],
        termAvailability=[],
        createdAt=datetime.now(),
        updatedAt=datetime.now(),
        sentiment=sentiment,
    )

    assert course_with_sent.sentiment is not None
    assert course_with_sent.sentiment.difficultyAvg == 3.5


# ============================================================================
# Pagination Schema Tests
# ============================================================================

def test_pagination_params_defaults():
    """Test pagination params with defaults"""
    params = PaginationParams()

    assert params.cursor is None
    assert params.limit == 50


def test_pagination_params_custom():
    """Test pagination params with custom values"""
    params = PaginationParams(cursor="Science:272:abc", limit=100)

    assert params.cursor == "Science:272:abc"
    assert params.limit == 100


def test_pagination_params_invalid_limit():
    """Test pagination params with invalid limit"""
    with pytest.raises(ValidationError):
        PaginationParams(limit=150)  # Max is 100


# ============================================================================
# Filter Schema Tests
# ============================================================================

def test_course_filters():
    """Test course filters"""
    filters = CourseFilters(
        faculty="Science",
        subject="CMPUT",
        minGpa=3.0,
        maxDifficulty=3.5,
        term="Fall",
    )

    assert filters.faculty == "Science"
    assert filters.minGpa == 3.0


def test_course_filters_partial():
    """Test course filters with partial data"""
    filters = CourseFilters(subject="CMPUT")

    assert filters.subject == "CMPUT"
    assert filters.faculty is None


# ============================================================================
# Search Schema Tests
# ============================================================================

def test_search_query():
    """Test search query schema"""
    query = SearchQuery(
        query="machine learning",
        filters=CourseFilters(subject="CMPUT"),
        limit=10,
    )

    assert query.query == "machine learning"
    assert query.filters.subject == "CMPUT"


def test_search_query_invalid():
    """Test search query with invalid data"""
    with pytest.raises(ValidationError):
        SearchQuery(query="", limit=10)  # Empty query not allowed


# ============================================================================
# Response Schema Tests
# ============================================================================

def test_course_list_response():
    """Test course list response"""
    course = CourseWithSentiment(
        id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        subject="CMPUT",
        number=272,
        title="Test",
        description="Test",
        credits=3.0,
        faculty="Science",
        prerequisiteCodes=[],
        termAvailability=[],
        createdAt=datetime.now(),
        updatedAt=datetime.now(),
        sentiment=None,
    )

    response = CourseListResponse(
        courses=[course],
        pagination=PaginationMeta(
            cursor=None,
            nextCursor="Science:272:abc",
            limit=50,
            hasMore=True,
        ),
    )

    assert len(response.courses) == 1
    assert response.pagination.hasMore is True


# ============================================================================
# Prerequisite Schema Tests
# ============================================================================

def test_prerequisite_node():
    """Test prerequisite node (recursive)"""
    course = Course(
        id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        subject="CMPUT",
        number=272,
        title="Test",
        description="Test",
        credits=3.0,
        faculty="Science",
        prerequisiteCodes=[],
        termAvailability=[],
        createdAt=datetime.now(),
        updatedAt=datetime.now(),
    )

    # Create nested structure
    child_node = PrerequisiteNode(course=course, children=[])
    parent_node = PrerequisiteNode(course=course, children=[child_node])

    assert len(parent_node.children) == 1
    assert parent_node.children[0].course.subject == "CMPUT"


# ============================================================================
# Scrape Schema Tests
# ============================================================================

def test_scrape_job_request():
    """Test scrape job request"""
    request = ScrapeJobRequest(
        subject="CMPUT",
        number=272,
        term="Fall 2024",
        force=True,
    )

    assert request.subject == "CMPUT"
    assert request.force is True


def test_scrape_job_response():
    """Test scrape job response"""
    response = ScrapeJobResponse(
        jobId="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        status="queued",
        message="Job queued",
    )

    assert response.status == "queued"


# ============================================================================
# Health Schema Tests
# ============================================================================

def test_health_response():
    """Test health response"""
    health = HealthResponse(
        status=HealthStatus.HEALTHY,
        database="healthy",
        redis="healthy",
        version="1.0.0",
        uptimeSeconds=3600.0,
    )

    assert health.status == HealthStatus.HEALTHY
    assert health.database == "healthy"


# ============================================================================
# Error Schema Tests
# ============================================================================

def test_error_response():
    """Test error response"""
    error = ErrorResponse(
        code="NOT_FOUND",
        message="Course not found",
        path="/api/v1/courses/CMPUT/999",
    )

    assert error.code == "NOT_FOUND"


def test_validation_error_response():
    """Test validation error response"""
    from app.schemas.contracts import ValidationErrorDetail

    error = ValidationErrorResponse(
        code="VALIDATION_ERROR",
        message="Validation failed",
        errors=[
            ValidationErrorDetail(
                field="number",
                message="must be >= 100",
                code="value_error.number.not_ge",
            )
        ],
    )

    assert error.code == "VALIDATION_ERROR"
    assert len(error.errors) == 1


# ============================================================================
# JSON Serialization Tests
# ============================================================================

def test_course_json_serialization():
    """Test course can be serialized to JSON"""
    course = Course(
        id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        subject="CMPUT",
        number=272,
        title="Test",
        description="Test",
        credits=3.0,
        faculty="Science",
        prerequisiteCodes=[],
        termAvailability=[],
        createdAt=datetime.now(),
        updatedAt=datetime.now(),
    )

    json_data = course.model_dump(by_alias=True)

    assert json_data["subject"] == "CMPUT"
    assert "prerequisiteCodes" in json_data  # Uses alias


def test_search_result_json_serialization():
    """Test search result serialization"""
    result = CourseSearchResult(
        id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        subject="CMPUT",
        number=272,
        title="Test",
        description="Test",
        credits=3.0,
        faculty="Science",
        prerequisiteCodes=[],
        termAvailability=[],
        createdAt=datetime.now(),
        updatedAt=datetime.now(),
        sentiment=None,
        relevanceScore=0.85,
        reasoning="High match",
    )

    json_data = result.model_dump(by_alias=True)

    assert json_data["relevanceScore"] == 0.85
    assert "reasoning" in json_data
