"""
Query Understanding and Intent Extraction

This module uses Claude to parse natural language course search queries
and extract structured search parameters and filters.

Examples:
- "easy 300-level CMPUT courses" → {level: [300], subject: "CMPUT", max_difficulty: 2.5}
- "high GPA machine learning courses" → {min_gpa: 3.3, keywords: ["machine learning"]}
- "what to take after CMPUT 272 and 274?" → {completed_courses: ["CMPUT 272", "CMPUT 274"]}
"""

import json
from typing import Any, Dict, List, Optional

import structlog
from anthropic import AsyncAnthropic
from pydantic import BaseModel, Field

from app.config import settings

logger = structlog.get_logger()


class QueryIntent(BaseModel):
    """Structured representation of query intent"""

    completed_courses: List[str] = Field(
        default_factory=list,
        description="Courses the student has completed",
    )
    target_area: Optional[str] = Field(
        None,
        description="Area of interest (e.g., 'machine learning', 'web development')",
    )
    difficulty_preference: Optional[str] = Field(
        None,
        description="Difficulty preference: 'easy', 'moderate', 'challenging'",
    )
    gpa_preference: Optional[float] = Field(
        None,
        description="Minimum desired GPA estimate",
    )
    term_preference: Optional[str] = Field(
        None,
        description="Preferred term: 'Fall', 'Winter', 'Spring/Summer'",
    )
    level_preference: Optional[List[int]] = Field(
        None,
        description="Preferred course levels (100, 200, 300, 400)",
    )
    subject_preference: Optional[str] = Field(
        None,
        description="Preferred subject code (e.g., 'CMPUT', 'MATH')",
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Key topics and keywords",
    )


class QueryParser:
    """
    Parse natural language queries into structured search parameters.

    Uses Claude to understand query intent and extract:
    - Completed courses (for prerequisite planning)
    - Target areas and keywords
    - Difficulty and GPA preferences
    - Term and level preferences
    - Subject filters
    """

    def __init__(self, anthropic_client: Optional[AsyncAnthropic] = None):
        """
        Initialize the query parser.

        Args:
            anthropic_client: Anthropic client (optional, creates default)
        """
        self.anthropic = anthropic_client or AsyncAnthropic(
            api_key=settings.anthropic_api_key
        )
        self.log = logger.bind(service="query_parser")

    async def parse_query(self, query: str) -> QueryIntent:
        """
        Parse natural language query into structured intent.

        Args:
            query: Natural language search query

        Returns:
            QueryIntent object with extracted parameters

        Examples:
            >>> await parser.parse_query("easy programming courses")
            QueryIntent(
                difficulty_preference="easy",
                keywords=["programming"],
                ...
            )
        """
        system_prompt = """You are a query parser for a university course search system.
Extract structured search parameters from student queries.

Return valid JSON matching this schema:
{
  "completed_courses": ["CMPUT 101", ...],  // courses mentioned as already taken
  "target_area": "machine learning",  // main area of interest
  "difficulty_preference": "easy" | "moderate" | "challenging" | null,
  "gpa_preference": 3.3,  // minimum desired GPA (null if not mentioned)
  "term_preference": "Fall" | "Winter" | "Spring/Summer" | null,
  "level_preference": [100, 200, 300, 400],  // course levels (null if not mentioned)
  "subject_preference": "CMPUT",  // subject code (null if not mentioned)
  "keywords": ["programming", "algorithms"]  // key topics
}

Guidelines:
- "easy", "bird", "low difficulty" → difficulty_preference: "easy"
- "challenging", "hard", "rigorous" → difficulty_preference: "challenging"
- "high GPA", "easy A" → gpa_preference: 3.3+
- "CMPUT", "computing science" → subject_preference: "CMPUT"
- "300-level", "third year" → level_preference: [300]
- "after CMPUT 272" → completed_courses: ["CMPUT 272"]"""

        user_prompt = f'Parse this query: "{query}"'

        try:
            response = await self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            response_text = response.content[0].text

            # Extract JSON from response
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            intent_data = json.loads(response_text)
            intent = QueryIntent(**intent_data)

            self.log.info(
                "query_parsed",
                query=query[:50],
                intent=intent.model_dump(),
            )

            return intent

        except json.JSONDecodeError as e:
            self.log.error(
                "query_parse_json_error",
                query=query[:50],
                error=str(e),
            )
            # Return minimal intent
            return QueryIntent(keywords=[query])

        except Exception as e:
            self.log.error(
                "query_parse_failed",
                query=query[:50],
                error=str(e),
            )
            # Return minimal intent
            return QueryIntent(keywords=[query])

    def intent_to_filters(self, intent: QueryIntent) -> Dict[str, Any]:
        """
        Convert QueryIntent to database filters.

        Args:
            intent: Parsed query intent

        Returns:
            Dict of filters compatible with CourseSearchService
        """
        filters = {}

        # Subject filter
        if intent.subject_preference:
            filters["subject"] = intent.subject_preference

        # Difficulty filter
        if intent.difficulty_preference:
            if intent.difficulty_preference == "easy":
                filters["max_difficulty"] = 2.5
            elif intent.difficulty_preference == "moderate":
                filters["max_difficulty"] = 3.5
            # "challenging" doesn't add a filter (allow all difficulties)

        # GPA filter
        if intent.gpa_preference:
            filters["min_gpa"] = intent.gpa_preference

        # Term filter
        if intent.term_preference:
            filters["term"] = intent.term_preference

        # Level filter (handled differently - would need custom SQL)
        if intent.level_preference:
            filters["level_preference"] = intent.level_preference

        self.log.debug(
            "intent_converted_to_filters",
            intent=intent.model_dump(),
            filters=filters,
        )

        return filters

    async def expand_query(self, query: str, initial_results_count: int) -> str:
        """
        Generate a broader query when initial search returns few results.

        Uses Claude to suggest query expansion with relaxed constraints.

        Args:
            query: Original query
            initial_results_count: Number of results from initial search

        Returns:
            Expanded query string
        """
        if initial_results_count >= 3:
            return query  # No need to expand

        system_prompt = """You are a search assistant helping students find courses.
When a query returns few results, suggest a broader version that relaxes constraints
while preserving the core intent."""

        user_prompt = f"""The query "{query}" returned only {initial_results_count} results.

Suggest a broader search query that:
1. Keeps the core topic/subject
2. Relaxes difficulty constraints
3. Expands to adjacent course levels
4. Includes related keywords

Return only the expanded query text, no explanation."""

        try:
            response = await self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=200,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            expanded_query = response.content[0].text.strip()

            self.log.info(
                "query_expanded",
                original_query=query[:50],
                expanded_query=expanded_query[:50],
                initial_results=initial_results_count,
            )

            return expanded_query

        except Exception as e:
            self.log.error(
                "query_expansion_failed",
                query=query[:50],
                error=str(e),
            )
            return query  # Return original on failure
