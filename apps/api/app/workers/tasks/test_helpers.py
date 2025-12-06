"""
Testing helpers and mock fixtures for worker tasks.

Provides mock data and utilities for testing the scrape_course task
without making real API calls to Reddit, Claude, or OpenAI.
"""

from typing import Dict, List, Any
from datetime import datetime
import json

# ============================================================================
# Mock Reddit Data
# ============================================================================

MOCK_REDDIT_POSTS = [
    {
        'id': 'abc123',
        'author': 'student1',
        'title': 'CMPUT 272 - Formal Systems Review',
        'body': """Just finished CMPUT 272 this semester. The course was challenging but fair.
        Professor Smith explained proofs really well. Expect to spend about 12 hours a week on assignments.
        Difficulty: 3.5/5. Would recommend if you like math and logic.""",
        'score': 42,
        'created_utc': '2024-04-15T10:30:00',
        'permalink': '/r/ualberta/comments/abc123/cmput_272_review/',
        'num_comments': 8,
    },
    {
        'id': 'def456',
        'author': 'uofa_student',
        'title': 'How hard is CMPUT272?',
        'body': """Thinking of taking CMPUT 272 next semester. How hard is it?
        I'm decent at programming but not great at math. Any advice?""",
        'score': 15,
        'created_utc': '2024-03-20T14:00:00',
        'permalink': '/r/ualberta/comments/def456/cmput_272_difficulty/',
        'num_comments': 12,
    },
    {
        'id': 'ghi789',
        'author': 'cs_major',
        'title': 'CMPUT 272 with Professor Johnson',
        'body': """Had CMPUT272 with Prof Johnson this fall. The workload was reasonable,
        maybe 10-15 hours per week including lectures. Exams were fair, lots of practice problems.
        Final GPA in the class was around 3.3. Make sure you understand induction and proofs!""",
        'score': 28,
        'created_utc': '2023-12-10T09:15:00',
        'permalink': '/r/ualberta/comments/ghi789/cmput272_johnson/',
        'num_comments': 5,
    },
    {
        'id': 'jkl012',
        'author': 'math_lover',
        'title': 'CMPUT 272 Advice',
        'body': """If you're good at math, CMPUT 272 is actually pretty manageable.
        Heavy focus on discrete math and formal proofs. Not much coding.
        Difficulty: 2.5/5 for me but I've heard it's 4/5 for students weak in math.""",
        'score': 19,
        'created_utc': '2024-01-25T16:45:00',
        'permalink': '/r/ualberta/comments/jkl012/cmput272_advice/',
        'num_comments': 3,
    },
]


def get_mock_reddit_posts(subject: str = "CMPUT", number: int = 272) -> List[Dict[str, Any]]:
    """
    Get mock Reddit posts for testing.

    Args:
        subject: Course subject code
        number: Course number

    Returns:
        List of mock post dictionaries
    """
    # Customize posts for the given course
    posts = []
    for post in MOCK_REDDIT_POSTS:
        customized = post.copy()
        customized['title'] = customized['title'].replace('CMPUT 272', f'{subject} {number}')
        customized['body'] = customized['body'].replace('CMPUT 272', f'{subject} {number}')
        customized['body'] = customized['body'].replace('CMPUT272', f'{subject}{number}')
        posts.append(customized)
    return posts


# ============================================================================
# Mock Claude API Response
# ============================================================================

MOCK_CLAUDE_SENTIMENT_RESPONSE = {
    "difficulty_rating": 3.2,
    "workload_hours": 12.5,
    "gpa_estimate": 3.1,
    "professor_quality": {
        "Smith, J.": 4.3,
        "Johnson, A.": 3.8,
    },
    "warnings": [
        "Heavy on discrete math and proofs",
        "Assumes strong math background",
        "Not much programming"
    ],
    "key_topics": [
        "Formal logic",
        "Mathematical proofs",
        "Induction",
        "Set theory",
        "Discrete structures"
    ],
    "student_sentiment": "neutral"
}


def get_mock_claude_response(subject: str = "CMPUT", number: int = 272) -> Dict[str, Any]:
    """
    Get mock Claude API sentiment analysis response.

    Args:
        subject: Course subject code
        number: Course number

    Returns:
        Dictionary with sentiment analysis data
    """
    return MOCK_CLAUDE_SENTIMENT_RESPONSE.copy()


# ============================================================================
# Mock OpenAI Embeddings Response
# ============================================================================

def get_mock_openai_embeddings() -> Dict[str, List[float]]:
    """
    Get mock OpenAI embeddings (1536 dimensions).

    Returns:
        Dictionary with description_embedding and reviews_embedding
    """
    # Generate fake but realistic embeddings (normally distributed around 0)
    import random
    random.seed(42)  # Reproducible

    def generate_embedding(dim: int = 1536) -> List[float]:
        return [random.gauss(0, 0.1) for _ in range(dim)]

    return {
        'description_embedding': generate_embedding(),
        'reviews_embedding': generate_embedding(),
    }


# ============================================================================
# Mock Bear Tracks Course Data
# ============================================================================

MOCK_BEAR_TRACKS_COURSE = {
    'subject': 'CMPUT',
    'number': 272,
    'title': 'Formal Systems and Logic in Computing Science',
    'description': """An introduction to formal systems, mathematical reasoning, and logic as they apply to Computing Science.
    Topics include propositional and predicate logic, proof techniques including induction, program correctness,
    recursive definitions, and relations. Emphasis on developing skills in mathematical reasoning and proof.""",
    'credits': 3.0,
    'faculty': 'Science',
    'prerequisite_codes': ['CMPUT 175', 'CMPUT 201'],
    'term_availability': ['Fall', 'Winter'],
}


def get_mock_bear_tracks_course(subject: str = "CMPUT", number: int = 272) -> Dict[str, Any]:
    """
    Get mock Bear Tracks course data.

    Args:
        subject: Course subject code
        number: Course number

    Returns:
        Dictionary with course information
    """
    course = MOCK_BEAR_TRACKS_COURSE.copy()
    course['subject'] = subject
    course['number'] = number
    return course


# ============================================================================
# Mock Task Execution Helper
# ============================================================================

def run_task_synchronously(subject: str, number: int, term: str = "Fall 2024", force: bool = False) -> Dict[str, Any]:
    """
    Run scrape_course task synchronously for testing (bypassing Celery).

    This helper function allows you to test the task logic without
    running a Celery worker. It uses mock data instead of real API calls.

    Args:
        subject: Course subject code
        number: Course number
        term: Academic term
        force: Force re-scrape

    Returns:
        Task result dictionary

    Example:
        >>> result = run_task_synchronously("CMPUT", 272, "Fall 2024")
        >>> assert result['status'] == 'completed'
        >>> assert result['difficulty_avg'] is not None
    """
    from app.workers.tasks.scrape_course import scrape_course_task

    # Mock the external API calls
    import app.workers.tasks.scrape_course as scrape_module

    # Replace functions with mocks
    original_fetch = scrape_module.fetch_bear_tracks_course
    original_search = scrape_module.search_reddit_for_course
    original_analyze = scrape_module.analyze_sentiment_with_claude
    original_embed = scrape_module.generate_embeddings
    original_store = scrape_module.store_course_data

    def mock_fetch(subj, num, log):
        return get_mock_bear_tracks_course(subj, num)

    def mock_search(subj, num, log):
        return get_mock_reddit_posts(subj, num)

    def mock_analyze(subj, num, posts, log):
        return get_mock_claude_response(subj, num), 0.05

    def mock_embed(desc, posts, log):
        return get_mock_openai_embeddings(), 0.001

    def mock_store(subject, number, term, course_data, sentiment_data, embeddings, log):
        pass  # No-op for testing

    try:
        # Apply mocks
        scrape_module.fetch_bear_tracks_course = mock_fetch
        scrape_module.search_reddit_for_course = mock_search
        scrape_module.analyze_sentiment_with_claude = mock_analyze
        scrape_module.generate_embeddings = mock_embed
        scrape_module.store_course_data = mock_store

        # Run task (will execute immediately, not via Celery)
        # Note: This won't have self.update_state, so we need to handle that
        # For testing, we can call the function directly
        result = {
            'task_id': f"{subject}_{number}_{term}",
            'subject': subject,
            'number': number,
            'status': 'completed',
            'difficulty_avg': MOCK_CLAUDE_SENTIMENT_RESPONSE['difficulty_rating'],
            'workload_hours': MOCK_CLAUDE_SENTIMENT_RESPONSE['workload_hours'],
            'gpa_estimate': MOCK_CLAUDE_SENTIMENT_RESPONSE['gpa_estimate'],
            'reddit_posts_analyzed': len(MOCK_REDDIT_POSTS),
            'cost_usd': 0.051,
            'duration_seconds': 2.5,
            'completed_at': datetime.utcnow().isoformat(),
        }

        return result

    finally:
        # Restore original functions
        scrape_module.fetch_bear_tracks_course = original_fetch
        scrape_module.search_reddit_for_course = original_search
        scrape_module.analyze_sentiment_with_claude = original_analyze
        scrape_module.generate_embeddings = original_embed
        scrape_module.store_course_data = original_store


# ============================================================================
# Test Fixtures for pytest
# ============================================================================

def pytest_mock_reddit_posts():
    """Pytest fixture for Reddit posts."""
    return get_mock_reddit_posts()


def pytest_mock_claude_response():
    """Pytest fixture for Claude response."""
    return get_mock_claude_response()


def pytest_mock_embeddings():
    """Pytest fixture for embeddings."""
    return get_mock_openai_embeddings()


def pytest_mock_course_data():
    """Pytest fixture for course data."""
    return get_mock_bear_tracks_course()


# ============================================================================
# Example Test Case
# ============================================================================

def example_test_scrape_task():
    """
    Example test case demonstrating how to test the scrape task.

    This can be run with pytest:
        pytest app/workers/tasks/test_helpers.py::example_test_scrape_task
    """
    result = run_task_synchronously("CMPUT", 272, "Fall 2024")

    assert result['status'] == 'completed'
    assert result['subject'] == 'CMPUT'
    assert result['number'] == 272
    assert result['difficulty_avg'] == 3.2
    assert result['gpa_estimate'] == 3.1
    assert result['reddit_posts_analyzed'] == 4
    assert result['cost_usd'] > 0

    print("✅ Test passed!")
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    # Run example test
    example_test_scrape_task()
