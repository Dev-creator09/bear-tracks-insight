"""
Course API endpoints (V1)
Implements comprehensive course discovery with pagination and filtering
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.dependencies import DbSession
from app.models import Course as CourseModel, CourseSentiment as SentimentModel
from app.schemas.contracts import (
    Course,
    CourseWithSentiment,
    CourseDetailResponse,
    CourseListResponse,
    PaginationParams,
    PaginationMeta,
    CourseFilters,
    PrerequisiteRef,
    CourseSentiment,
)

router = APIRouter()


def build_cursor(faculty: str, number: int, id: str) -> str:
    """Build cursor string for pagination"""
    return f"{faculty}:{number}:{id}"


def parse_cursor(cursor: str) -> tuple[str, int, str]:
    """Parse cursor string"""
    try:
        parts = cursor.split(":")
        if len(parts) != 3:
            raise ValueError("Invalid cursor format")
        return parts[0], int(parts[1]), parts[2]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid cursor: {str(e)}")


def convert_course_to_schema(course: CourseModel) -> CourseWithSentiment:
    """Convert SQLAlchemy model to Pydantic schema"""
    course_dict = {
        "id": str(course.id),
        "subject": course.subject,
        "number": course.number,
        "title": course.title,
        "description": course.description,
        "credits": course.credits,
        "faculty": course.faculty,
        "prerequisiteCodes": course.prerequisitesCodes or [],
        "termAvailability": course.termAvailability or [],
        "createdAt": course.createdAt,
        "updatedAt": course.updatedAt,
        "sentiment": None,
    }

    if hasattr(course, "sentiment") and course.sentiment:
        sent = course.sentiment
        course_dict["sentiment"] = {
            "id": str(sent.id),
            "courseId": str(sent.courseId),
            "redditThreadIds": sent.redditThreadIds or [],
            "difficultyAvg": sent.difficultyAvg,
            "workloadAvg": sent.workloadAvg,
            "gpaEstimate": sent.gpaEstimate,
            "professorMentions": sent.professorMentions,
            "warnings": sent.warnings or [],
            "lastScrapedAt": sent.lastScrapedAt,
        }

    return CourseWithSentiment(**course_dict)


@router.get("/courses", response_model=CourseListResponse)
async def list_courses(
    db: DbSession,
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    limit: int = Query(50, ge=1, le=100, description="Results per page"),
    faculty: Optional[str] = Query(None, description="Filter by faculty"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    min_gpa: Optional[float] = Query(None, ge=0, le=4, alias="min_gpa"),
    max_difficulty: Optional[float] = Query(None, ge=1, le=5, alias="max_difficulty"),
    term: Optional[str] = Query(None, description="Filter by term"),
) -> CourseListResponse:
    """
    List courses with pagination and filters.

    Uses cursor-based pagination for efficient large dataset traversal.
    """
    # Build query
    query = select(CourseModel).options(selectinload(CourseModel.sentiment))

    # Apply filters
    filters = []

    if faculty:
        filters.append(CourseModel.faculty == faculty)

    if subject:
        filters.append(CourseModel.subject == subject)

    if term:
        filters.append(CourseModel.termAvailability.contains([term]))

    # Sentiment filters (requires join)
    if min_gpa is not None or max_difficulty is not None:
        query = query.join(SentimentModel, CourseModel.id == SentimentModel.courseId)

        if min_gpa is not None:
            filters.append(SentimentModel.gpaEstimate >= min_gpa)

        if max_difficulty is not None:
            filters.append(SentimentModel.difficultyAvg <= max_difficulty)

    if filters:
        query = query.where(and_(*filters))

    # Handle cursor pagination
    if cursor:
        cursor_faculty, cursor_number, cursor_id = parse_cursor(cursor)
        query = query.where(
            or_(
                and_(
                    CourseModel.faculty == cursor_faculty,
                    CourseModel.number > cursor_number,
                ),
                CourseModel.faculty > cursor_faculty,
            )
        )

    # Order and limit
    query = query.order_by(CourseModel.faculty, CourseModel.number).limit(limit + 1)

    # Execute query
    result = await db.execute(query)
    courses = result.scalars().all()

    # Determine if there are more results
    has_more = len(courses) > limit
    if has_more:
        courses = courses[:limit]

    # Build next cursor
    next_cursor = None
    if has_more and courses:
        last_course = courses[-1]
        next_cursor = build_cursor(last_course.faculty, last_course.number, str(last_course.id))

    # Convert to schemas
    course_schemas = [convert_course_to_schema(course) for course in courses]

    return CourseListResponse(
        courses=course_schemas,
        pagination=PaginationMeta(
            cursor=cursor,
            nextCursor=next_cursor,
            limit=limit,
            hasMore=has_more,
        ),
    )


@router.get("/courses/{subject}/{number}", response_model=CourseDetailResponse)
async def get_course_detail(
    subject: str,
    number: int,
    db: DbSession,
) -> CourseDetailResponse:
    """
    Get detailed course information including sentiment and prerequisites.
    """
    # Query course with all relationships
    query = (
        select(CourseModel)
        .where(and_(CourseModel.subject == subject, CourseModel.number == number))
        .options(
            selectinload(CourseModel.sentiment),
            selectinload(CourseModel.prerequisites).selectinload("requiredCourse"),
            selectinload(CourseModel.requiredBy).selectinload("course"),
        )
    )

    result = await db.execute(query)
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(
            status_code=404, detail=f"Course {subject} {number} not found"
        )

    # Convert base course
    course_dict = convert_course_to_schema(course).model_dump()

    # Add prerequisites
    prerequisites = []
    if hasattr(course, "prerequisites"):
        for prereq in course.prerequisites:
            if hasattr(prereq, "requiredCourse"):
                req_course = prereq.requiredCourse
                prerequisites.append(
                    PrerequisiteRef(
                        id=str(prereq.id),
                        course=Course(
                            id=str(req_course.id),
                            subject=req_course.subject,
                            number=req_course.number,
                            title=req_course.title,
                            description=req_course.description,
                            credits=req_course.credits,
                            faculty=req_course.faculty,
                            prerequisiteCodes=req_course.prerequisitesCodes or [],
                            termAvailability=req_course.termAvailability or [],
                            createdAt=req_course.createdAt,
                            updatedAt=req_course.updatedAt,
                        ),
                    )
                )

    # Add required by
    required_by = []
    if hasattr(course, "requiredBy"):
        for req in course.requiredBy:
            if hasattr(req, "course"):
                req_course = req.course
                required_by.append(
                    PrerequisiteRef(
                        id=str(req.id),
                        course=Course(
                            id=str(req_course.id),
                            subject=req_course.subject,
                            number=req_course.number,
                            title=req_course.title,
                            description=req_course.description,
                            credits=req_course.credits,
                            faculty=req_course.faculty,
                            prerequisiteCodes=req_course.prerequisitesCodes or [],
                            termAvailability=req_course.termAvailability or [],
                            createdAt=req_course.createdAt,
                            updatedAt=req_course.updatedAt,
                        ),
                    )
                )

    return CourseDetailResponse(
        **course_dict,
        prerequisites=prerequisites,
        requiredBy=required_by,
    )
