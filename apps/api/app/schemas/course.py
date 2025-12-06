"""Course-related Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CourseBase(BaseModel):
    """Base course schema."""

    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    credits: int = Field(..., ge=1, le=12)
    department: str = Field(..., min_length=1, max_length=100)
    level: int = Field(..., ge=100, le=999)


class CourseCreate(CourseBase):
    """Schema for creating a course."""
    pass


class CourseUpdate(BaseModel):
    """Schema for updating a course."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    credits: Optional[int] = Field(None, ge=1, le=12)
    department: Optional[str] = Field(None, min_length=1, max_length=100)
    level: Optional[int] = Field(None, ge=100, le=999)


class CourseSentimentResponse(BaseModel):
    """Schema for course sentiment response."""

    id: int
    rating: float
    difficulty: float
    workload: float
    sentiment_score: float
    created_at: datetime

    model_config = {"from_attributes": True}


class CourseResponse(CourseBase):
    """Schema for course response."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
