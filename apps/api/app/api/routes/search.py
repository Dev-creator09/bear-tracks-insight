"""
Semantic search endpoints
Implements AI-powered course search using RAG pipeline with hybrid search and LLM re-ranking
"""

import structlog
from fastapi import APIRouter, HTTPException, Depends
from redis.asyncio import Redis

from app.dependencies import DbSession
from app.services.rag import CourseSearchService
from app.services.query_parser import QueryParser
from app.schemas.contracts import (
    SearchQuery,
    CourseSearchResponse,
    CourseSearchResult,
    CourseSentiment,
)
from app.config import settings

router = APIRouter()
logger = structlog.get_logger()


async def get_redis() -> Redis:
    """Get Redis client dependency."""
    redis_client = Redis.from_url(settings.redis_url, decode_responses=False)
    try:
        yield redis_client
    finally:
        await redis_client.close()


@router.post("/courses/search", response_model=CourseSearchResponse)
async def search_courses(
    query_data: SearchQuery,
    db: DbSession,
    redis: Redis = Depends(get_redis),
) -> CourseSearchResponse:
    """
    AI-powered semantic search for courses using RAG pipeline.

    This endpoint implements a sophisticated hybrid search approach:
    1. Query parsing to understand intent (difficulty preferences, GPA goals, etc.)
    2. Hybrid search combining:
       - Vector similarity search using OpenAI embeddings + pgvector
       - Keyword-based full-text search using PostgreSQL tsvector
       - Reciprocal rank fusion to merge results
    3. LLM-based re-ranking using Claude for intent-aware ordering
    4. Self-reflection to broaden search if results are sparse

    Returns ranked results with relevance scores, reasoning, and metadata.

    Args:
        query_data: Search query with optional filters and limit
        db: Database session
        redis: Redis client for caching

    Returns:
        CourseSearchResponse with results, metadata, cost, and latency

    Raises:
        HTTPException: If search fails due to service errors
    """
    log = logger.bind(
        endpoint="search_courses",
        query=query_data.query[:50],
        filters=query_data.filters.model_dump() if query_data.filters else None,
    )

    try:
        # Initialize services
        search_service = CourseSearchService(db, redis)
        query_parser = QueryParser()

        # Parse query to extract filters (if not explicitly provided)
        if not query_data.filters or not any(
            [
                query_data.filters.faculty,
                query_data.filters.subject,
                query_data.filters.min_gpa,
                query_data.filters.max_difficulty,
                query_data.filters.term,
            ]
        ):
            try:
                intent = await query_parser.parse_query(query_data.query)
                parsed_filters = query_parser.intent_to_filters(intent)

                # Merge with explicit filters (explicit filters take precedence)
                if query_data.filters:
                    filters_dict = query_data.filters.model_dump(exclude_none=True)
                    parsed_filters.update(filters_dict)
                else:
                    filters_dict = parsed_filters
            except Exception as e:
                log.warning("query_parsing_failed", error=str(e))
                filters_dict = (
                    query_data.filters.model_dump(exclude_none=True)
                    if query_data.filters
                    else {}
                )
        else:
            filters_dict = query_data.filters.model_dump(exclude_none=True)

        # Execute search
        search_result = await search_service.search(
            query=query_data.query,
            filters=filters_dict,
            limit=query_data.limit,
        )

        # Convert results to response format
        results = []
        for course in search_result["results"]:
            # Build sentiment data if available
            sentiment_data = None
            if (
                course.get("difficulty_avg") is not None
                or course.get("gpa_estimate") is not None
            ):
                # Note: This is simplified - in production, fetch full sentiment from DB
                pass

            search_result_item = CourseSearchResult(
                id=course["id"],
                subject=course["subject"],
                number=course["number"],
                title=course["title"],
                description=course["description"],
                credits=course["credits"],
                faculty=course["faculty"],
                prerequisiteCodes=course.get("prerequisites_codes", []),
                termAvailability=course.get("term_availability", []),
                createdAt=None,  # Would need to fetch from DB
                updatedAt=None,  # Would need to fetch from DB
                sentiment=sentiment_data,
                relevanceScore=course.get("relevance_score", 0.0),
                reasoning=course.get("reasoning", ""),
            )
            results.append(search_result_item)

        log.info(
            "search_completed",
            num_results=len(results),
            cost_usd=search_result["cost_usd"],
            latency_ms=search_result["latency_ms"],
        )

        return CourseSearchResponse(
            results=results,
            query=query_data.query,
            totalResults=search_result["total"],
            filtersApplied=search_result["filters_applied"],
            costUsd=search_result["cost_usd"],
            latencyMs=search_result["latency_ms"],
        )

    except Exception as e:
        log.error("search_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}",
        )
