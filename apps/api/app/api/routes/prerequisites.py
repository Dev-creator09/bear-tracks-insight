"""
Prerequisite tree endpoints
Implements recursive prerequisite graph traversal
"""

from typing import List, Dict, Set
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.dependencies import DbSession
from app.models import Course as CourseModel, Prerequisite as PrerequisiteModel
from app.schemas.contracts import (
    Course,
    PrerequisiteNode,
    PrerequisiteTreeResponse,
)

router = APIRouter()


async def build_prerequisite_tree(
    course_id: str,
    db: DbSession,
    current_depth: int,
    max_depth: int,
    visited: Set[str],
) -> PrerequisiteNode:
    """
    Recursively build prerequisite tree up to max depth.
    Uses visited set to prevent infinite loops.
    """
    # Prevent infinite loops
    if current_depth >= max_depth or course_id in visited:
        # Get course without recursing
        result = await db.execute(
            select(CourseModel).where(CourseModel.id == course_id)
        )
        course = result.scalar_one_or_none()

        if not course:
            raise HTTPException(status_code=404, detail="Course not found in tree")

        return PrerequisiteNode(
            course=Course(
                id=str(course.id),
                subject=course.subject,
                number=course.number,
                title=course.title,
                description=course.description,
                credits=course.credits,
                faculty=course.faculty,
                prerequisiteCodes=course.prerequisitesCodes or [],
                termAvailability=course.termAvailability or [],
                createdAt=course.createdAt,
                updatedAt=course.updatedAt,
            ),
            children=[],
        )

    visited.add(course_id)

    # Get course with prerequisites
    result = await db.execute(
        select(CourseModel)
        .where(CourseModel.id == course_id)
        .options(selectinload(CourseModel.prerequisites))
    )
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Build children recursively
    children = []
    if hasattr(course, "prerequisites"):
        for prereq_rel in course.prerequisites:
            # Get the prerequisite course
            prereq_result = await db.execute(
                select(CourseModel).where(CourseModel.id == prereq_rel.requiresId)
            )
            prereq_course = prereq_result.scalar_one_or_none()

            if prereq_course:
                child_node = await build_prerequisite_tree(
                    str(prereq_course.id),
                    db,
                    current_depth + 1,
                    max_depth,
                    visited,
                )
                children.append(child_node)

    return PrerequisiteNode(
        course=Course(
            id=str(course.id),
            subject=course.subject,
            number=course.number,
            title=course.title,
            description=course.description,
            credits=course.credits,
            faculty=course.faculty,
            prerequisiteCodes=course.prerequisitesCodes or [],
            termAvailability=course.termAvailability or [],
            createdAt=course.createdAt,
            updatedAt=course.updatedAt,
        ),
        children=children,
    )


@router.get("/prerequisites/{subject}/{number}", response_model=PrerequisiteTreeResponse)
async def get_prerequisite_tree(
    subject: str,
    number: int,
    db: DbSession,
    depth: int = Query(5, ge=1, le=10, description="Maximum tree depth"),
) -> PrerequisiteTreeResponse:
    """
    Get the complete prerequisite tree for a course.

    Returns a nested tree structure showing all prerequisite courses
    and their dependencies up to the specified depth.
    """
    # Find the course
    result = await db.execute(
        select(CourseModel).where(
            and_(CourseModel.subject == subject, CourseModel.number == number)
        )
    )
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(
            status_code=404, detail=f"Course {subject} {number} not found"
        )

    # Build the tree
    visited: Set[str] = set()
    tree = await build_prerequisite_tree(str(course.id), db, 0, depth, visited)

    return PrerequisiteTreeResponse(
        course=Course(
            id=str(course.id),
            subject=course.subject,
            number=course.number,
            title=course.title,
            description=course.description,
            credits=course.credits,
            faculty=course.faculty,
            prerequisiteCodes=course.prerequisitesCodes or [],
            termAvailability=course.termAvailability or [],
            createdAt=course.createdAt,
            updatedAt=course.updatedAt,
        ),
        tree=tree,
        depth=depth,
    )
