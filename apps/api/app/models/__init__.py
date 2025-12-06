"""SQLAlchemy models."""

from app.database import Base
from app.models.course import Course, CourseSentiment, CourseEmbedding, Prerequisite

__all__ = ["Base", "Course", "CourseSentiment", "CourseEmbedding", "Prerequisite"]
