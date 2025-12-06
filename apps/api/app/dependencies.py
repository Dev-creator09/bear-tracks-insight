"""Dependency injection utilities."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

# Common dependency annotations
DbSession = Annotated[AsyncSession, Depends(get_db)]
