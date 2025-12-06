"""Course-related SQLAlchemy models."""

from datetime import datetime
from typing import List

from sqlalchemy import (
    String,
    Integer,
    Float,
    Text,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.database import Base


class Course(Base):
    """Course model."""

    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    credits: Mapped[int] = mapped_column(Integer, nullable=False)
    department: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    sentiments: Mapped[List["CourseSentiment"]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )
    embeddings: Mapped[List["CourseEmbedding"]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )
    prerequisites: Mapped[List["Prerequisite"]] = relationship(
        foreign_keys="Prerequisite.course_id",
        back_populates="course",
        cascade="all, delete-orphan",
    )
    required_for: Mapped[List["Prerequisite"]] = relationship(
        foreign_keys="Prerequisite.prerequisite_id",
        back_populates="prerequisite_course",
    )

    __table_args__ = (
        Index("idx_course_dept_level", "department", "level"),
    )


class CourseSentiment(Base):
    """Course sentiment analysis model."""

    __tablename__ = "course_sentiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )

    rating: Mapped[float] = mapped_column(Float, nullable=False)
    difficulty: Mapped[float] = mapped_column(Float, nullable=False)
    workload: Mapped[float] = mapped_column(Float, nullable=False)
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False)
    review_text: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    course: Mapped["Course"] = relationship(back_populates="sentiments")

    __table_args__ = (
        Index("idx_sentiment_course", "course_id"),
        Index("idx_sentiment_rating", "rating"),
    )


class CourseEmbedding(Base):
    """Course embedding vectors for semantic search."""

    __tablename__ = "course_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    embedding: Mapped[Vector] = mapped_column(Vector(1536), nullable=False)  # OpenAI ada-002 dimensions

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    course: Mapped["Course"] = relationship(back_populates="embeddings")


class Prerequisite(Base):
    """Course prerequisite relationships."""

    __tablename__ = "prerequisites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    prerequisite_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )

    is_required: Mapped[bool] = mapped_column(default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    course: Mapped["Course"] = relationship(
        foreign_keys=[course_id], back_populates="prerequisites"
    )
    prerequisite_course: Mapped["Course"] = relationship(
        foreign_keys=[prerequisite_id], back_populates="required_for"
    )

    __table_args__ = (
        Index("idx_prereq_course", "course_id"),
        Index("idx_prereq_prerequisite", "prerequisite_id"),
    )
