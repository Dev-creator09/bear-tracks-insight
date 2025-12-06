"""Course endpoints."""

from typing import List

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.dependencies import DbSession
from app.models import Course
from app.schemas.course import CourseCreate, CourseResponse, CourseUpdate

router = APIRouter()


@router.get("/courses", response_model=List[CourseResponse])
async def list_courses(
    db: DbSession,
    skip: int = 0,
    limit: int = 100,
    department: str | None = None,
) -> List[Course]:
    """
    List all courses with optional filtering.

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **department**: Filter by department name
    """
    query = select(Course).offset(skip).limit(limit)

    if department:
        query = query.where(Course.department == department)

    result = await db.execute(query)
    courses = result.scalars().all()

    return list(courses)


@router.get("/courses/{course_id}", response_model=CourseResponse)
async def get_course(course_id: int, db: DbSession) -> Course:
    """
    Get a specific course by ID.

    - **course_id**: The ID of the course to retrieve
    """
    result = await db.execute(
        select(Course)
        .where(Course.id == course_id)
        .options(selectinload(Course.sentiments))
    )
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    return course


@router.post("/courses", response_model=CourseResponse, status_code=201)
async def create_course(course: CourseCreate, db: DbSession) -> Course:
    """
    Create a new course.

    - **course**: Course data to create
    """
    # Check if course code already exists
    result = await db.execute(select(Course).where(Course.code == course.code))
    existing_course = result.scalar_one_or_none()

    if existing_course:
        raise HTTPException(
            status_code=400,
            detail=f"Course with code {course.code} already exists"
        )

    db_course = Course(**course.model_dump())
    db.add(db_course)
    await db.flush()
    await db.refresh(db_course)

    return db_course


@router.patch("/courses/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    course_update: CourseUpdate,
    db: DbSession,
) -> Course:
    """
    Update a course.

    - **course_id**: The ID of the course to update
    - **course_update**: Updated course data
    """
    result = await db.execute(select(Course).where(Course.id == course_id))
    db_course = result.scalar_one_or_none()

    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")

    update_data = course_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_course, field, value)

    await db.flush()
    await db.refresh(db_course)

    return db_course


@router.delete("/courses/{course_id}", status_code=204)
async def delete_course(course_id: int, db: DbSession) -> None:
    """
    Delete a course.

    - **course_id**: The ID of the course to delete
    """
    result = await db.execute(select(Course).where(Course.id == course_id))
    db_course = result.scalar_one_or_none()

    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")

    await db.delete(db_course)
