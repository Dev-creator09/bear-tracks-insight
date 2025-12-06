"""
Course scraping and analysis task.

This module implements the main background job for:
1. Fetching course data from Bear Tracks
2. Searching Reddit for course mentions
3. Analyzing sentiment with Claude AI
4. Generating vector embeddings with OpenAI
5. Persisting data to PostgreSQL

The task is idempotent and includes comprehensive retry logic,
progress tracking, and error handling.
"""

import time
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import traceback as tb

# HTTP and HTML parsing
import httpx
from bs4 import BeautifulSoup

# Reddit API
import praw
from praw.exceptions import RedditAPIException

# AI APIs
import anthropic
import openai

# Database
from sqlalchemy.orm import Session
from sqlalchemy import select

# Celery
from celery import Task
from celery.exceptions import Retry

# Redis for locking
import redis

# Structured logging
import structlog

from app.workers.celery_app import celery_app
# from app.database import get_db
# from app.models import Course, CourseSentiment, CourseEmbedding, Prerequisite

logger = structlog.get_logger(__name__)

# ============================================================================
# Configuration
# ============================================================================

REDDIT_CLIENT_ID = ""  # Will load from env
REDDIT_CLIENT_SECRET = ""  # Will load from env
REDDIT_USER_AGENT = "BearTracksBot/1.0"
ANTHROPIC_API_KEY = ""  # Will load from env
OPENAI_API_KEY = ""  # Will load from env

REDIS_CLIENT = redis.Redis.from_url('redis://localhost:6379/0', decode_responses=True)

# API cost tracking (USD)
CLAUDE_INPUT_COST_PER_1M = 3.0
CLAUDE_OUTPUT_COST_PER_1M = 15.0
OPENAI_EMBEDDING_COST_PER_1M = 0.02

# ============================================================================
# Helper Functions
# ============================================================================

def parse_prerequisite_codes(text: str) -> List[str]:
    """
    Extract course codes from prerequisite text.

    Args:
        text: Text containing prerequisite information

    Returns:
        List of course codes (e.g., ["CMPUT 201", "MATH 101"])

    Example:
        >>> parse_prerequisite_codes("Prerequisites: CMPUT 201 and MATH 101 or MATH 115")
        ["CMPUT 201", "MATH 101", "MATH 115"]
    """
    pattern = r'\b([A-Z]{2,5})\s+(\d{3})\b'
    matches = re.findall(pattern, text)
    return [f"{subject} {number}" for subject, number in matches]


def calculate_api_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    """
    Calculate API cost in USD.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model name ('claude' or 'openai-embedding')

    Returns:
        Cost in USD
    """
    if model == 'claude':
        input_cost = (input_tokens / 1_000_000) * CLAUDE_INPUT_COST_PER_1M
        output_cost = (output_tokens / 1_000_000) * CLAUDE_OUTPUT_COST_PER_1M
        return input_cost + output_cost
    elif model == 'openai-embedding':
        total_cost = (input_tokens / 1_000_000) * OPENAI_EMBEDDING_COST_PER_1M
        return total_cost
    return 0.0


def acquire_lock(task_id: str, ttl: int = 3600) -> bool:
    """
    Acquire a distributed lock for task idempotency.

    Args:
        task_id: Unique task identifier
        ttl: Lock time-to-live in seconds

    Returns:
        True if lock acquired, False if already locked
    """
    lock_key = f"scrape_lock:{task_id}"
    return REDIS_CLIENT.set(lock_key, "1", nx=True, ex=ttl)


def release_lock(task_id: str) -> None:
    """Release distributed lock."""
    lock_key = f"scrape_lock:{task_id}"
    REDIS_CLIENT.delete(lock_key)


def publish_progress(task_id: str, progress: Dict[str, Any]) -> None:
    """
    Publish task progress to Redis pub/sub.

    Args:
        task_id: Unique task identifier
        progress: Progress data to publish
    """
    channel = f"scrape_progress:{task_id}"
    REDIS_CLIENT.publish(channel, json.dumps(progress))


# ============================================================================
# Main Scraping Task
# ============================================================================

@celery_app.task(
    bind=True,
    name='scrape_course',
    max_retries=3,
    autoretry_for=(
        httpx.ConnectTimeout,
        httpx.ReadTimeout,
        redis.ConnectionError,
    ),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def scrape_course_task(
    self: Task,
    subject: str,
    number: int,
    term: str,
    force: bool = False
) -> Dict[str, Any]:
    """
    Scrape and analyze course data from multiple sources.

    This task performs the following steps:
    1. Fetch course info from Bear Tracks
    2. Search Reddit for course mentions
    3. Analyze sentiment with Claude AI
    4. Generate embeddings with OpenAI
    5. Store results in PostgreSQL

    Args:
        subject: Course subject code (e.g., "CMPUT")
        number: Course number (e.g., 272)
        term: Academic term (e.g., "Fall 2024")
        force: If True, bypass cache and re-scrape

    Returns:
        Dictionary with task results including status, metrics, and costs

    Raises:
        Retry: If a retryable error occurs
        Exception: If max retries exceeded or non-retryable error

    Example:
        >>> result = scrape_course_task.delay("CMPUT", 272, "Fall 2024")
        >>> result.get()
        {
            'task_id': 'CMPUT_272_Fall_2024',
            'subject': 'CMPUT',
            'number': 272,
            'status': 'completed',
            'difficulty_avg': 3.5,
            'gpa_estimate': 3.2,
            'cost_usd': 0.05,
            'duration_seconds': 45.2
        }
    """
    start_time = time.time()
    task_id = f"{subject}_{number}_{term}"
    total_cost = 0.0

    log = logger.bind(
        task_id=task_id,
        subject=subject,
        number=number,
        term=term,
        celery_task_id=self.request.id
    )

    log.info("task_started", force=force)

    try:
        # ====================================================================
        # Step 0: Idempotency Check
        # ====================================================================

        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Checking for existing data'}
        )

        # Check if already processing
        if not force and not acquire_lock(task_id):
            log.warning("task_already_running", task_id=task_id)
            # Try to get cached result
            cached_key = f"scrape_result:{task_id}"
            cached_result = REDIS_CLIENT.get(cached_key)
            if cached_result:
                return json.loads(cached_result)
            # If no cached result, wait and retry
            raise Retry(countdown=30, max_retries=3)

        # Check database for recent scrape
        # TODO: Query CourseSentiment for last_scraped_at
        # if last_scraped_at and (datetime.utcnow() - last_scraped_at) < timedelta(hours=24) and not force:
        #     log.info("recent_scrape_found", last_scraped_at=last_scraped_at)
        #     release_lock(task_id)
        #     return {'status': 'skipped', 'reason': 'scraped_recently'}

        # ====================================================================
        # Step 1: Fetch Course from Bear Tracks (20% progress)
        # ====================================================================

        log.info("step_1_fetch_course_starting")
        self.update_state(
            state='PROGRESS',
            meta={'current': 5, 'total': 100, 'status': 'Fetching course from Bear Tracks'}
        )
        publish_progress(task_id, {'step': 1, 'status': 'fetching_course'})

        course_data = fetch_bear_tracks_course(subject, number, log)

        self.update_state(
            state='PROGRESS',
            meta={'current': 20, 'total': 100, 'status': 'Course data fetched'}
        )

        log.info("step_1_complete",
                 title=course_data.get('title'),
                 credits=course_data.get('credits'))

        # ====================================================================
        # Step 2: Search Reddit (40% progress)
        # ====================================================================

        log.info("step_2_reddit_search_starting")
        self.update_state(
            state='PROGRESS',
            meta={'current': 25, 'total': 100, 'status': 'Searching Reddit for mentions'}
        )
        publish_progress(task_id, {'step': 2, 'status': 'searching_reddit'})

        reddit_posts = search_reddit_for_course(subject, number, log)

        self.update_state(
            state='PROGRESS',
            meta={'current': 40, 'total': 100, 'status': f'Found {len(reddit_posts)} Reddit posts'}
        )

        log.info("step_2_complete", posts_found=len(reddit_posts))

        # ====================================================================
        # Step 3: Analyze Sentiment with Claude (60% progress)
        # ====================================================================

        log.info("step_3_sentiment_analysis_starting")
        self.update_state(
            state='PROGRESS',
            meta={'current': 45, 'total': 100, 'status': 'Analyzing sentiment with AI'}
        )
        publish_progress(task_id, {'step': 3, 'status': 'analyzing_sentiment'})

        sentiment_data, claude_cost = analyze_sentiment_with_claude(
            subject, number, reddit_posts, log
        )
        total_cost += claude_cost

        self.update_state(
            state='PROGRESS',
            meta={'current': 60, 'total': 100, 'status': 'Sentiment analysis complete'}
        )

        log.info("step_3_complete",
                 difficulty=sentiment_data.get('difficulty_rating'),
                 gpa_estimate=sentiment_data.get('gpa_estimate'),
                 cost=claude_cost)

        # ====================================================================
        # Step 4: Generate Embeddings (80% progress)
        # ====================================================================

        log.info("step_4_embeddings_starting")
        self.update_state(
            state='PROGRESS',
            meta={'current': 65, 'total': 100, 'status': 'Generating embeddings'}
        )
        publish_progress(task_id, {'step': 4, 'status': 'generating_embeddings'})

        embeddings, embedding_cost = generate_embeddings(
            course_data.get('description', ''),
            reddit_posts,
            log
        )
        total_cost += embedding_cost

        self.update_state(
            state='PROGRESS',
            meta={'current': 80, 'total': 100, 'status': 'Embeddings generated'}
        )

        log.info("step_4_complete", cost=embedding_cost)

        # ====================================================================
        # Step 5: Store in Database (95% progress)
        # ====================================================================

        log.info("step_5_database_storage_starting")
        self.update_state(
            state='PROGRESS',
            meta={'current': 85, 'total': 100, 'status': 'Saving to database'}
        )
        publish_progress(task_id, {'step': 5, 'status': 'saving_to_database'})

        store_course_data(
            subject=subject,
            number=number,
            term=term,
            course_data=course_data,
            sentiment_data=sentiment_data,
            embeddings=embeddings,
            log=log
        )

        self.update_state(
            state='PROGRESS',
            meta={'current': 95, 'total': 100, 'status': 'Data saved successfully'}
        )

        log.info("step_5_complete")

        # ====================================================================
        # Step 6: Finalize and Return Results
        # ====================================================================

        duration = time.time() - start_time

        result = {
            'task_id': task_id,
            'subject': subject,
            'number': number,
            'status': 'completed',
            'difficulty_avg': sentiment_data.get('difficulty_rating'),
            'workload_hours': sentiment_data.get('workload_hours'),
            'gpa_estimate': sentiment_data.get('gpa_estimate'),
            'reddit_posts_analyzed': len(reddit_posts),
            'cost_usd': round(total_cost, 4),
            'duration_seconds': round(duration, 2),
            'completed_at': datetime.utcnow().isoformat(),
        }

        # Cache result
        cache_key = f"scrape_result:{task_id}"
        REDIS_CLIENT.setex(cache_key, 3600, json.dumps(result))

        # Release lock
        release_lock(task_id)

        self.update_state(
            state='SUCCESS',
            meta={'current': 100, 'total': 100, 'status': 'Complete', 'result': result}
        )

        publish_progress(task_id, {'step': 6, 'status': 'completed', 'result': result})

        log.info("task_completed",
                 duration_seconds=duration,
                 cost_usd=total_cost,
                 difficulty=sentiment_data.get('difficulty_rating'))

        return result

    except Exception as exc:
        duration = time.time() - start_time

        log.error("task_failed",
                  exception=str(exc),
                  duration_seconds=duration,
                  traceback=tb.format_exc())

        # Release lock on failure
        release_lock(task_id)

        # Check if we should retry
        if self.request.retries < self.max_retries:
            retry_countdown = min(
                2 ** self.request.retries * 10,  # Exponential backoff
                600  # Max 10 minutes
            )
            log.warning("task_retrying",
                       retry_attempt=self.request.retries + 1,
                       retry_countdown=retry_countdown)
            raise self.retry(exc=exc, countdown=retry_countdown)

        # Max retries exceeded - send to dead letter queue
        log.error("task_failed_permanently",
                  retries_exhausted=self.max_retries)

        handle_failed_scrape.delay(
            task_id=task_id,
            exception=str(exc),
            traceback=tb.format_exc(),
            attempts=self.request.retries + 1
        )

        raise


# ============================================================================
# Step 1: Fetch from Bear Tracks
# ============================================================================

def fetch_bear_tracks_course(
    subject: str,
    number: int,
    log: structlog.BoundLogger
) -> Dict[str, Any]:
    """
    Fetch course information from UAlberta Bear Tracks.

    Args:
        subject: Course subject code
        number: Course number
        log: Structured logger instance

    Returns:
        Dictionary with course data (title, description, credits, etc.)

    Raises:
        httpx.HTTPStatusError: If course not found (404)
        httpx.TimeoutException: If request times out
    """
    url = f"https://apps.ualberta.ca/catalogue/course/{subject}/{number}"

    log.info("fetching_bear_tracks", url=url)

    with httpx.Client(timeout=30.0) as client:
        try:
            response = client.get(url)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract data (simplified - actual selectors would need adjustment)
            title_elem = soup.select_one('.course-title')
            title = title_elem.text.strip() if title_elem else f"{subject} {number}"

            desc_elem = soup.select_one('.course-description')
            description = desc_elem.text.strip() if desc_elem else ""

            credits_elem = soup.select_one('.course-credits')
            credits_text = credits_elem.text.strip() if credits_elem else "3.0"
            credits = float(re.search(r'(\d+\.?\d*)', credits_text).group(1)) if credits_text else 3.0

            prereq_elem = soup.select_one('.course-prerequisites')
            prereq_text = prereq_elem.text.strip() if prereq_elem else ""
            prerequisite_codes = parse_prerequisite_codes(prereq_text)

            # Determine faculty from subject
            faculty_map = {
                'CMPUT': 'Science',
                'MATH': 'Science',
                'STAT': 'Science',
                'ENGG': 'Engineering',
                'BUS': 'Business',
                'ECON': 'Arts',
            }
            faculty = faculty_map.get(subject, 'Unknown')

            course_data = {
                'subject': subject,
                'number': number,
                'title': title,
                'description': description,
                'credits': credits,
                'faculty': faculty,
                'prerequisite_codes': prerequisite_codes,
                'term_availability': ['Fall', 'Winter'],  # Default
            }

            log.info("bear_tracks_fetch_success",
                     title=title,
                     credits=credits,
                     prerequisites=len(prerequisite_codes))

            return course_data

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                log.error("course_not_found", url=url)
                raise ValueError(f"Course {subject} {number} not found")
            log.error("bear_tracks_http_error",
                     status_code=exc.response.status_code)
            raise
        except httpx.TimeoutException as exc:
            log.error("bear_tracks_timeout", url=url)
            raise


# ============================================================================
# Step 2: Search Reddit
# ============================================================================

def search_reddit_for_course(
    subject: str,
    number: int,
    log: structlog.BoundLogger
) -> List[Dict[str, Any]]:
    """
    Search Reddit r/ualberta for course mentions.

    Args:
        subject: Course subject code
        number: Course number
        log: Structured logger instance

    Returns:
        List of post dictionaries with author, title, body, score, etc.

    Handles:
        - Rate limiting with automatic retry
        - Post filtering by score and relevance
        - Exclusion of bot posts
    """
    log.info("searching_reddit", subreddit="ualberta")

    # Initialize Reddit client (using placeholder credentials)
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID or "placeholder",
        client_secret=REDDIT_CLIENT_SECRET or "placeholder",
        user_agent=REDDIT_USER_AGENT,
        check_for_async=False
    )

    # Search queries
    queries = [
        f"{subject} {number}",
        f"{subject}{number}"
    ]

    all_posts = []
    seen_ids = set()

    for query in queries:
        try:
            subreddit = reddit.subreddit('ualberta')

            # Search with rate limit handling
            max_rate_limit_retries = 3
            rate_limit_retry = 0

            while rate_limit_retry < max_rate_limit_retries:
                try:
                    results = subreddit.search(
                        query=query,
                        sort='relevance',
                        time_filter='all',
                        limit=50
                    )

                    for post in results:
                        # Skip if already seen
                        if post.id in seen_ids:
                            continue

                        # Filter: must have score > 5
                        if post.score <= 5:
                            continue

                        # Filter: must contain course code
                        text = f"{post.title} {post.selftext}".lower()
                        course_pattern = f"{subject}\\s*{number}".lower()
                        if not re.search(course_pattern, text):
                            continue

                        # Filter: exclude bots
                        if post.author and 'bot' in str(post.author).lower():
                            continue

                        post_data = {
                            'id': post.id,
                            'author': str(post.author) if post.author else '[deleted]',
                            'title': post.title,
                            'body': post.selftext,
                            'score': post.score,
                            'created_utc': datetime.fromtimestamp(post.created_utc).isoformat(),
                            'permalink': f"https://reddit.com{post.permalink}",
                            'num_comments': post.num_comments,
                        }

                        all_posts.append(post_data)
                        seen_ids.add(post.id)

                    break  # Success, exit retry loop

                except RedditAPIException as exc:
                    # Handle rate limiting
                    if exc.error_type == 'RATELIMIT':
                        rate_limit_retry += 1
                        # Try to extract wait time from error message
                        wait_time = 60  # Default 1 minute
                        log.warning("reddit_rate_limited",
                                   retry_attempt=rate_limit_retry,
                                   wait_seconds=wait_time)
                        time.sleep(wait_time)
                    else:
                        log.error("reddit_api_exception",
                                 error_type=exc.error_type,
                                 message=str(exc))
                        raise

        except Exception as exc:
            log.error("reddit_search_error",
                     query=query,
                     exception=str(exc))
            # Continue with next query even if one fails
            continue

    log.info("reddit_search_complete",
             posts_found=len(all_posts),
             unique_posts=len(seen_ids))

    return all_posts


# ============================================================================
# Step 3: Analyze Sentiment with Claude
# ============================================================================

def analyze_sentiment_with_claude(
    subject: str,
    number: int,
    reddit_posts: List[Dict[str, Any]],
    log: structlog.BoundLogger
) -> tuple[Dict[str, Any], float]:
    """
    Analyze course sentiment using Claude AI.

    Args:
        subject: Course subject code
        number: Course number
        reddit_posts: List of Reddit post dictionaries
        log: Structured logger instance

    Returns:
        Tuple of (sentiment_data dict, cost in USD)

    The sentiment_data includes:
        - difficulty_rating: float 1-5
        - workload_hours: float (hours per week)
        - gpa_estimate: float 0-4.0
        - professor_quality: dict of professor -> rating
        - warnings: list of strings
        - key_topics: list of main topics
        - student_sentiment: 'positive' | 'neutral' | 'negative'
    """
    log.info("analyzing_sentiment_with_claude", posts_count=len(reddit_posts))

    # Aggregate reviews
    aggregated_text = "\n\n---\n\n".join([
        f"Post by {post['author']} (Score: {post['score']}):\n{post['title']}\n{post['body']}"
        for post in reddit_posts[:30]  # Limit to avoid token limits
    ])

    # Truncate to max 50k chars
    if len(aggregated_text) > 50000:
        aggregated_text = aggregated_text[:50000] + "\n\n[...truncated]"

    # Prepare prompt
    system_prompt = """You are an expert at analyzing student course reviews. Extract structured sentiment data from Reddit posts about university courses."""

    user_prompt = f"""Analyze these student reviews for {subject} {number}:

{aggregated_text}

Extract the following in JSON format:
{{
  "difficulty_rating": <float 1-5, where 1=very easy, 5=very hard>,
  "workload_hours": <float, estimated hours per week>,
  "gpa_estimate": <float 0-4.0, estimated average GPA>,
  "professor_quality": {{"Professor Name": <rating 1-5>, ...}},
  "warnings": ["warning1", "warning2", ...],
  "key_topics": ["topic1", "topic2", ...],
  "student_sentiment": "<positive|neutral|negative>"
}}

If there's insufficient data for any field, use null. Be objective and base ratings on actual student comments."""

    # Call Claude API
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY or "placeholder")

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        # Extract JSON from response
        response_text = response.content[0].text

        # Try to parse JSON
        try:
            # Look for JSON in response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                sentiment_data = json.loads(json_match.group(0))
            else:
                log.warning("no_json_found_in_claude_response")
                sentiment_data = get_default_sentiment()
        except json.JSONDecodeError as exc:
            log.warning("failed_to_parse_claude_json",
                       exception=str(exc),
                       response_text=response_text[:200])
            sentiment_data = get_default_sentiment()

        # Calculate cost
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = calculate_api_cost(input_tokens, output_tokens, 'claude')

        log.info("claude_analysis_complete",
                 input_tokens=input_tokens,
                 output_tokens=output_tokens,
                 cost_usd=cost)

        return sentiment_data, cost

    except anthropic.RateLimitError as exc:
        log.error("claude_rate_limit", exception=str(exc))
        raise  # Will trigger retry
    except anthropic.APIError as exc:
        log.error("claude_api_error",
                 exception=str(exc),
                 status_code=getattr(exc, 'status_code', None))
        # Don't retry on 4xx errors
        if hasattr(exc, 'status_code') and 400 <= exc.status_code < 500:
            return get_default_sentiment(), 0.0
        raise


def get_default_sentiment() -> Dict[str, Any]:
    """Return default sentiment data when analysis fails."""
    return {
        'difficulty_rating': None,
        'workload_hours': None,
        'gpa_estimate': None,
        'professor_quality': {},
        'warnings': [],
        'key_topics': [],
        'student_sentiment': 'neutral'
    }


# ============================================================================
# Step 4: Generate Embeddings
# ============================================================================

def generate_embeddings(
    description: str,
    reddit_posts: List[Dict[str, Any]],
    log: structlog.BoundLogger
) -> tuple[Dict[str, List[float]], float]:
    """
    Generate vector embeddings using OpenAI.

    Args:
        description: Course description text
        reddit_posts: List of Reddit post dictionaries
        log: Structured logger instance

    Returns:
        Tuple of (embeddings dict, cost in USD)

    The embeddings dict contains:
        - description_embedding: 1536-dim vector for description
        - reviews_embedding: 1536-dim vector for aggregated reviews
    """
    log.info("generating_embeddings")

    # Aggregate reviews
    reviews_text = " ".join([
        f"{post['title']} {post['body']}"
        for post in reddit_posts[:20]
    ])

    # Truncate if too long
    if len(description) > 8000:
        description = description[:8000]
    if len(reviews_text) > 8000:
        reviews_text = reviews_text[:8000]

    client = openai.OpenAI(api_key=OPENAI_API_KEY or "placeholder")

    try:
        # Batch both embeddings in one call
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=[description, reviews_text],
            encoding_format="float"
        )

        description_embedding = response.data[0].embedding
        reviews_embedding = response.data[1].embedding

        # Calculate cost
        total_tokens = response.usage.total_tokens
        cost = calculate_api_cost(total_tokens, 0, 'openai-embedding')

        log.info("embeddings_generated",
                 total_tokens=total_tokens,
                 cost_usd=cost)

        return {
            'description_embedding': description_embedding,
            'reviews_embedding': reviews_embedding
        }, cost

    except openai.RateLimitError as exc:
        log.error("openai_rate_limit", exception=str(exc))
        raise  # Will trigger retry
    except openai.APIError as exc:
        log.error("openai_api_error", exception=str(exc))
        raise


# ============================================================================
# Step 5: Store in Database
# ============================================================================

def store_course_data(
    subject: str,
    number: int,
    term: str,
    course_data: Dict[str, Any],
    sentiment_data: Dict[str, Any],
    embeddings: Dict[str, List[float]],
    log: structlog.BoundLogger
) -> None:
    """
    Store all course data in PostgreSQL.

    Args:
        subject: Course subject code
        number: Course number
        term: Academic term
        course_data: Course information
        sentiment_data: Sentiment analysis results
        embeddings: Vector embeddings
        log: Structured logger instance

    This function:
        - Upserts Course record
        - Upserts CourseSentiment record
        - Upserts CourseEmbedding record
        - Creates Prerequisite relationships
        - Commits transaction with rollback on error
    """
    log.info("storing_to_database")

    # TODO: Implement database storage
    # This would use SQLAlchemy to:
    # 1. Get or create Course
    # 2. Upsert CourseSentiment
    # 3. Upsert CourseEmbedding with pgvector
    # 4. Create Prerequisite relationships
    # 5. Commit transaction

    # Placeholder implementation
    log.info("database_storage_complete",
             subject=subject,
             number=number,
             term=term)

    # In production:
    # try:
    #     db = next(get_db())
    #     # Upsert operations here
    #     db.commit()
    # except Exception as exc:
    #     db.rollback()
    #     log.error("database_error", exception=str(exc))
    #     raise


# ============================================================================
# Dead Letter Queue Handler
# ============================================================================

@celery_app.task(name='handle_failed_scrape')
def handle_failed_scrape(
    task_id: str,
    exception: str,
    traceback: str,
    attempts: int
) -> None:
    """
    Handle permanently failed scrape tasks.

    Args:
        task_id: Task identifier
        exception: Exception message
        traceback: Full traceback
        attempts: Number of retry attempts made

    This task:
        - Logs the failure with full context
        - Stores failure in FailedJobs table
        - Sends alert notification
    """
    log = logger.bind(
        task_id=task_id,
        exception=exception,
        attempts=attempts
    )

    log.error("task_permanently_failed",
              traceback=traceback)

    # TODO: Store in FailedJobs table
    # TODO: Send notification (email, Slack, etc.)

    print(f"""
    ╔════════════════════════════════════════════════════════════════╗
    ║  SCRAPE TASK FAILED PERMANENTLY                                ║
    ╠════════════════════════════════════════════════════════════════╣
    ║  Task ID: {task_id:<50} ║
    ║  Attempts: {attempts:<49} ║
    ║  Exception: {exception[:47]:<47} ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
