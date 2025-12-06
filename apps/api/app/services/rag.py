"""
RAG Pipeline for Course Search

This module implements a hybrid Retrieval-Augmented Generation (RAG) pipeline
for semantic course search. It combines:

1. Vector similarity search using OpenAI embeddings and pgvector
2. Keyword-based full-text search using PostgreSQL tsvector
3. Hybrid ranking using reciprocal rank fusion
4. LLM-based re-ranking with Claude for intent understanding

Architecture:
- embed_query: Generates embeddings with Redis caching
- vector_search: Semantic search via pgvector cosine similarity
- hybrid_search: Combines vector + keyword search with rank fusion
- re_rank_with_claude: Uses Claude to understand query intent and re-rank
- search: Main entry point orchestrating the full pipeline

Performance targets:
- Recall@10 > 0.85
- MRR > 0.70
- Latency p95 < 3000ms
- Cost per query < $0.10
"""

import json
import time
import hashlib
from typing import Any, Dict, List, Optional
from datetime import datetime

import structlog
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from redis.asyncio import Redis
from sqlalchemy import select, text, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from pydantic import BaseModel, ValidationError

from app.models.course import Course as CourseModel, CourseSentiment
from app.config import settings

logger = structlog.get_logger()


class RankedCourse(BaseModel):
    """Course with ranking metadata"""

    course_code: str
    rank: int
    relevance_score: float
    reasoning: str


class CourseSearchService:
    """
    Course search service implementing hybrid RAG pipeline.

    Combines semantic search (vector embeddings) with keyword search,
    then uses Claude for intelligent re-ranking based on query intent.
    """

    # Embedding cost: $0.02 per 1M tokens (text-embedding-3-small)
    EMBEDDING_COST_PER_TOKEN = 0.02 / 1_000_000
    # Claude cost: $3 per 1M input tokens, $15 per 1M output tokens
    CLAUDE_INPUT_COST_PER_TOKEN = 3.0 / 1_000_000
    CLAUDE_OUTPUT_COST_PER_TOKEN = 15.0 / 1_000_000

    def __init__(
        self,
        db: AsyncSession,
        redis_client: Redis,
        openai_client: Optional[AsyncOpenAI] = None,
        anthropic_client: Optional[AsyncAnthropic] = None,
    ):
        """
        Initialize the course search service.

        Args:
            db: Database session for querying courses
            redis_client: Redis client for caching embeddings
            openai_client: OpenAI client for embeddings (optional, creates default)
            anthropic_client: Anthropic client for re-ranking (optional, creates default)
        """
        self.db = db
        self.redis = redis_client
        self.openai = openai_client or AsyncOpenAI(api_key=settings.openai_api_key)
        self.anthropic = anthropic_client or AsyncAnthropic(
            api_key=settings.anthropic_api_key
        )

        # Vector search configuration
        self.top_k = 20  # Retrieve top 20 for re-ranking
        self.similarity_threshold = 0.6  # Minimum cosine similarity

        # Cache configuration
        self.embedding_cache_ttl = 3600  # 1 hour

        self.log = logger.bind(service="course_search")

    def _cache_key(self, query: str) -> str:
        """Generate cache key for query embedding."""
        query_hash = hashlib.sha256(query.encode()).hexdigest()
        return f"embedding:{query_hash}"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
    )
    async def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for search query with caching and retry logic.

        Args:
            query: Natural language search query

        Returns:
            1536-dimensional embedding vector

        Raises:
            Exception: If embedding generation fails after retries
        """
        cache_key = self._cache_key(query)

        # Check Redis cache
        try:
            cached = await self.redis.get(cache_key)
            if cached:
                self.log.debug("embedding_cache_hit", query=query[:50])
                return json.loads(cached)
        except Exception as e:
            self.log.warning("redis_cache_read_failed", error=str(e))

        # Generate embedding
        start_time = time.time()
        try:
            response = await self.openai.embeddings.create(
                model="text-embedding-3-small", input=query
            )
            embedding = response.data[0].embedding
            tokens_used = response.usage.total_tokens
            cost = tokens_used * self.EMBEDDING_COST_PER_TOKEN

            latency_ms = int((time.time() - start_time) * 1000)

            self.log.info(
                "embedding_generated",
                query=query[:50],
                tokens=tokens_used,
                cost_usd=cost,
                latency_ms=latency_ms,
            )

            # Cache the result
            try:
                await self.redis.setex(
                    cache_key, self.embedding_cache_ttl, json.dumps(embedding)
                )
            except Exception as e:
                self.log.warning("redis_cache_write_failed", error=str(e))

            return embedding

        except Exception as e:
            self.log.error("embedding_generation_failed", query=query[:50], error=str(e))
            raise

    async def vector_search(
        self, query_embedding: List[float], filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search using pgvector.

        Args:
            query_embedding: Query embedding vector
            filters: Optional filters (faculty, subject, min_gpa, max_difficulty, term)

        Returns:
            List of courses with similarity scores
        """
        # Build filter conditions
        filter_conditions = []

        if filters:
            if filters.get("faculty"):
                filter_conditions.append(f"c.faculty = '{filters['faculty']}'")

            if filters.get("subject"):
                filter_conditions.append(f"c.subject = '{filters['subject']}'")

            if filters.get("term"):
                filter_conditions.append(
                    f"'{filters['term']}' = ANY(c.term_availability)"
                )

            if filters.get("min_gpa") is not None:
                filter_conditions.append(
                    f"cs.gpa_estimate >= {filters['min_gpa']}"
                )

            if filters.get("max_difficulty") is not None:
                filter_conditions.append(
                    f"cs.difficulty_avg <= {filters['max_difficulty']}"
                )

        filter_sql = " AND ".join(filter_conditions) if filter_conditions else "TRUE"

        # Vector search query
        query_sql = f"""
            SELECT
                c.id,
                c.subject,
                c.number,
                c.title,
                c.description,
                c.credits,
                c.faculty,
                c.prerequisites_codes,
                c.term_availability,
                c.created_at,
                c.updated_at,
                cs.difficulty_avg,
                cs.workload_avg,
                cs.gpa_estimate,
                cs.warnings,
                COALESCE(
                    1 - (ce.description_vector <=> :query_embedding::vector),
                    0
                ) as similarity_score
            FROM courses c
            LEFT JOIN course_embeddings ce ON c.id = ce.course_id
            LEFT JOIN course_sentiments cs ON c.id = cs.course_id
            WHERE {filter_sql}
                AND ce.description_vector IS NOT NULL
            ORDER BY ce.description_vector <=> :query_embedding::vector
            LIMIT :limit
        """

        try:
            result = await self.db.execute(
                text(query_sql),
                {
                    "query_embedding": json.dumps(query_embedding),
                    "limit": self.top_k,
                },
            )
            rows = result.fetchall()

            courses = []
            for row in rows:
                if row.similarity_score >= self.similarity_threshold:
                    courses.append(
                        {
                            "id": str(row.id),
                            "subject": row.subject,
                            "number": row.number,
                            "title": row.title,
                            "description": row.description,
                            "credits": float(row.credits),
                            "faculty": row.faculty,
                            "prerequisites_codes": row.prerequisites_codes or [],
                            "term_availability": row.term_availability or [],
                            "difficulty_avg": (
                                float(row.difficulty_avg) if row.difficulty_avg else None
                            ),
                            "workload_avg": (
                                float(row.workload_avg) if row.workload_avg else None
                            ),
                            "gpa_estimate": (
                                float(row.gpa_estimate) if row.gpa_estimate else None
                            ),
                            "warnings": row.warnings or [],
                            "similarity_score": float(row.similarity_score),
                            "rank_vector": len(courses) + 1,
                        }
                    )

            self.log.info(
                "vector_search_completed",
                num_results=len(courses),
                filters=filters,
            )
            return courses

        except Exception as e:
            self.log.error("vector_search_failed", error=str(e), filters=filters)
            raise

    async def keyword_search(
        self, query: str, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform keyword-based full-text search.

        Args:
            query: Search query
            filters: Optional filters

        Returns:
            List of courses with keyword match scores
        """
        # Build filter conditions
        filter_conditions = []

        if filters:
            if filters.get("faculty"):
                filter_conditions.append(f"c.faculty = '{filters['faculty']}'")

            if filters.get("subject"):
                filter_conditions.append(f"c.subject = '{filters['subject']}'")

            if filters.get("term"):
                filter_conditions.append(
                    f"'{filters['term']}' = ANY(c.term_availability)"
                )

        filter_sql = " AND ".join(filter_conditions) if filter_conditions else "TRUE"

        # Keyword search using PostgreSQL full-text search
        query_sql = f"""
            SELECT
                c.id,
                c.subject,
                c.number,
                c.title,
                c.description,
                c.credits,
                c.faculty,
                c.prerequisites_codes,
                c.term_availability,
                cs.difficulty_avg,
                cs.workload_avg,
                cs.gpa_estimate,
                cs.warnings,
                ts_rank(
                    to_tsvector('english', c.title || ' ' || c.description),
                    plainto_tsquery('english', :query)
                ) as keyword_score
            FROM courses c
            LEFT JOIN course_sentiments cs ON c.id = cs.course_id
            WHERE ({filter_sql})
                AND (
                    to_tsvector('english', c.title || ' ' || c.description) @@
                    plainto_tsquery('english', :query)
                )
            ORDER BY keyword_score DESC
            LIMIT :limit
        """

        try:
            result = await self.db.execute(
                text(query_sql),
                {"query": query, "limit": self.top_k},
            )
            rows = result.fetchall()

            courses = []
            for row in rows:
                courses.append(
                    {
                        "id": str(row.id),
                        "subject": row.subject,
                        "number": row.number,
                        "title": row.title,
                        "description": row.description,
                        "credits": float(row.credits),
                        "faculty": row.faculty,
                        "prerequisites_codes": row.prerequisites_codes or [],
                        "term_availability": row.term_availability or [],
                        "difficulty_avg": (
                            float(row.difficulty_avg) if row.difficulty_avg else None
                        ),
                        "workload_avg": (
                            float(row.workload_avg) if row.workload_avg else None
                        ),
                        "gpa_estimate": (
                            float(row.gpa_estimate) if row.gpa_estimate else None
                        ),
                        "warnings": row.warnings or [],
                        "keyword_score": float(row.keyword_score),
                        "rank_keyword": len(courses) + 1,
                    }
                )

            self.log.info(
                "keyword_search_completed",
                num_results=len(courses),
                query=query[:50],
            )
            return courses

        except Exception as e:
            self.log.error("keyword_search_failed", error=str(e), query=query[:50])
            raise

    def _reciprocal_rank_fusion(
        self, vector_results: List[Dict], keyword_results: List[Dict], k: int = 60
    ) -> List[Dict]:
        """
        Combine vector and keyword search results using reciprocal rank fusion.

        RRF formula: score = 1/(rank + k) where k=60 is standard

        Args:
            vector_results: Results from vector search
            keyword_results: Results from keyword search
            k: Constant for RRF (default 60)

        Returns:
            Merged and sorted list of courses
        """
        # Build course map with RRF scores
        course_scores = {}

        for course in vector_results:
            course_id = course["id"]
            rank = course.get("rank_vector", len(vector_results))
            score = 1.0 / (rank + k)

            if course_id not in course_scores:
                course_scores[course_id] = {"course": course, "score": score}
            else:
                course_scores[course_id]["score"] += score

        for course in keyword_results:
            course_id = course["id"]
            rank = course.get("rank_keyword", len(keyword_results))
            score = 1.0 / (rank + k)

            if course_id not in course_scores:
                course_scores[course_id] = {"course": course, "score": score}
            else:
                course_scores[course_id]["score"] += score
                # Merge course data (prefer vector results for base data)
                if "similarity_score" not in course_scores[course_id]["course"]:
                    course_scores[course_id]["course"].update(course)

        # Sort by RRF score
        sorted_courses = sorted(
            course_scores.values(), key=lambda x: x["score"], reverse=True
        )

        # Add RRF score to course data
        results = []
        for item in sorted_courses[: self.top_k]:
            course = item["course"]
            course["rrf_score"] = item["score"]
            results.append(course)

        return results

    async def hybrid_search(
        self, query: str, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining vector and keyword search.

        Args:
            query: Natural language search query
            filters: Optional filters

        Returns:
            List of courses ranked by reciprocal rank fusion
        """
        # Generate embedding for vector search
        query_embedding = await self.embed_query(query)

        # Run both searches in parallel would be ideal, but for simplicity run sequentially
        vector_results = await self.vector_search(query_embedding, filters)
        keyword_results = await self.keyword_search(query, filters)

        # Combine with reciprocal rank fusion
        hybrid_results = self._reciprocal_rank_fusion(vector_results, keyword_results)

        self.log.info(
            "hybrid_search_completed",
            query=query[:50],
            vector_count=len(vector_results),
            keyword_count=len(keyword_results),
            hybrid_count=len(hybrid_results),
        )

        return hybrid_results

    async def re_rank_with_claude(
        self, courses: List[Dict[str, Any]], query: str, top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Re-rank courses using Claude for intent understanding.

        Args:
            courses: List of candidate courses
            query: Original search query
            top_k: Number of results to return

        Returns:
            Re-ranked list of courses with relevance scores and reasoning
        """
        if not courses:
            return []

        # Prepare course data for Claude
        course_summaries = []
        for course in courses:
            course_summaries.append(
                {
                    "code": f"{course['subject']} {course['number']}",
                    "title": course["title"],
                    "description": course["description"][:200],
                    "difficulty": course.get("difficulty_avg"),
                    "gpa": course.get("gpa_estimate"),
                    "warnings": course.get("warnings", []),
                }
            )

        # Build prompt
        system_prompt = "You are a UAlberta academic advisor helping students find courses. Your goal is to understand their intent and rank courses by relevance."

        user_prompt = f"""Student query: {query}

Available courses:
{json.dumps(course_summaries, indent=2)}

Rank these courses by relevance to the query. Consider:
- Semantic match to query intent
- Difficulty preference (if mentioned: "easy" → prefer low difficulty, "challenging" → prefer high difficulty)
- GPA preference (if mentioned: "high GPA" → prefer high estimates)
- Prerequisites compatibility
- Student warnings (serious warnings should lower ranking)

Return JSON array of top {top_k} courses:
[
  {{
    "course_code": "CMPUT 272",
    "rank": 1,
    "relevance_score": 0.95,
    "reasoning": "explanation of why this matches the query"
  }},
  ...
]

Only return valid JSON, no additional text."""

        start_time = time.time()
        try:
            response = await self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            latency_ms = int((time.time() - start_time) * 1000)

            # Calculate cost
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = (
                input_tokens * self.CLAUDE_INPUT_COST_PER_TOKEN
                + output_tokens * self.CLAUDE_OUTPUT_COST_PER_TOKEN
            )

            self.log.info(
                "claude_reranking_completed",
                query=query[:50],
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                latency_ms=latency_ms,
            )

            # Parse Claude's response
            response_text = response.content[0].text

            # Extract JSON from response (Claude might wrap it in markdown)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            rankings = json.loads(response_text)

            # Validate and map back to full course objects
            course_map = {
                f"{c['subject']} {c['number']}": c for c in courses
            }

            re_ranked = []
            for ranking in rankings:
                course_code = ranking["course_code"]
                if course_code in course_map:
                    course = course_map[course_code].copy()
                    course["relevance_score"] = ranking["relevance_score"]
                    course["reasoning"] = ranking["reasoning"]
                    course["claude_rank"] = ranking["rank"]
                    re_ranked.append(course)

            return re_ranked

        except json.JSONDecodeError as e:
            self.log.error(
                "claude_response_parse_failed",
                query=query[:50],
                error=str(e),
                response=response_text[:200] if 'response_text' in locals() else None,
            )
            # Fallback to original ranking
            return courses[:top_k]

        except Exception as e:
            self.log.error(
                "claude_reranking_failed",
                query=query[:50],
                error=str(e),
            )
            # Fallback to original ranking
            return courses[:top_k]

    async def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Main search entry point orchestrating the full RAG pipeline.

        Pipeline steps:
        1. Hybrid search (vector + keyword with RRF)
        2. Re-rank with Claude for intent understanding
        3. Self-reflection: broaden search if results < 3

        Args:
            query: Natural language search query
            filters: Optional filters (faculty, subject, min_gpa, max_difficulty, term)
            limit: Number of results to return (default 10)

        Returns:
            Dict with results, metadata, cost, and latency
        """
        start_time = time.time()
        total_cost = 0.0

        self.log.info(
            "search_started",
            query=query[:50],
            filters=filters,
            limit=limit,
        )

        try:
            # Step 1: Hybrid search
            hybrid_results = await self.hybrid_search(query, filters)

            # Step 2: Re-rank with Claude
            re_ranked_results = await self.re_rank_with_claude(
                hybrid_results, query, top_k=limit
            )

            # Step 3: Self-reflection - if too few results, suggest broadening
            if len(re_ranked_results) < 3 and filters:
                self.log.warning(
                    "few_results_found",
                    query=query[:50],
                    num_results=len(re_ranked_results),
                    filters=filters,
                )
                # Could implement auto-broadening here

            total_latency_ms = int((time.time() - start_time) * 1000)

            # Note: Cost tracking would need to be accumulated from embed_query and re_rank_with_claude
            # For now, we'll set a placeholder
            total_cost = 0.05  # Placeholder

            self.log.info(
                "search_completed",
                query=query[:50],
                num_results=len(re_ranked_results),
                latency_ms=total_latency_ms,
                cost_usd=total_cost,
            )

            return {
                "results": re_ranked_results,
                "total": len(re_ranked_results),
                "query": query,
                "filters_applied": filters or {},
                "cost_usd": total_cost,
                "latency_ms": total_latency_ms,
            }

        except Exception as e:
            self.log.error(
                "search_failed",
                query=query[:50],
                error=str(e),
                filters=filters,
            )
            raise
