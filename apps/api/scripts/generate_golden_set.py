"""
Golden Dataset Generation Script

This script helps generate a golden dataset of test queries with labeled
relevant courses for evaluation purposes.

The dataset is organized into categories:
1. Easy courses (queries about low-difficulty courses)
2. Prerequisite planning (queries about course sequences)
3. Specialization paths (queries about specific areas)
4. Professor-specific (queries about instructor quality)

Usage:
    python scripts/generate_golden_set.py

Output:
    apps/api/fixtures/golden-queries.json
"""

import json
from pathlib import Path
from typing import Dict, List

GOLDEN_QUERIES = [
    # Category 1: Easy Courses (10 queries)
    {
        "query": "easy CMPUT courses for beginners",
        "relevant_courses": ["CMPUT 101", "CMPUT 174", "CMPUT 175"],
        "category": "easy_courses",
        "expected_difficulty_range": [1.0, 2.5],
        "expected_gpa_range": [3.0, 4.0],
    },
    {
        "query": "low difficulty 200-level computing science",
        "relevant_courses": ["CMPUT 201", "CMPUT 204"],
        "category": "easy_courses",
        "expected_difficulty_range": [1.0, 2.5],
        "expected_gpa_range": [3.0, 4.0],
    },
    {
        "query": "bird courses in CS",
        "relevant_courses": ["CMPUT 101", "CMPUT 174"],
        "category": "easy_courses",
        "expected_difficulty_range": [1.0, 2.0],
        "expected_gpa_range": [3.3, 4.0],
    },
    {
        "query": "easy programming courses for non-majors",
        "relevant_courses": ["CMPUT 101", "CMPUT 174"],
        "category": "easy_courses",
        "expected_difficulty_range": [1.0, 2.0],
        "expected_gpa_range": None,
    },
    {
        "query": "introductory computing science with high GPA",
        "relevant_courses": ["CMPUT 101", "CMPUT 174", "CMPUT 175"],
        "category": "easy_courses",
        "expected_difficulty_range": [1.0, 2.5],
        "expected_gpa_range": [3.2, 4.0],
    },
    {
        "query": "simple 300-level CMPUT courses",
        "relevant_courses": ["CMPUT 301", "CMPUT 302"],
        "category": "easy_courses",
        "expected_difficulty_range": [1.0, 3.0],
        "expected_gpa_range": None,
    },
    {
        "query": "easiest upper-year computer science courses",
        "relevant_courses": ["CMPUT 301", "CMPUT 302", "CMPUT 304"],
        "category": "easy_courses",
        "expected_difficulty_range": [1.0, 2.5],
        "expected_gpa_range": [3.0, 4.0],
    },
    {
        "query": "beginner-friendly programming classes",
        "relevant_courses": ["CMPUT 101", "CMPUT 174", "CMPUT 175"],
        "category": "easy_courses",
        "expected_difficulty_range": [1.0, 2.0],
        "expected_gpa_range": None,
    },
    {
        "query": "less challenging computing courses",
        "relevant_courses": ["CMPUT 101", "CMPUT 201", "CMPUT 174"],
        "category": "easy_courses",
        "expected_difficulty_range": [1.0, 2.5],
        "expected_gpa_range": None,
    },
    {
        "query": "CMPUT courses with light workload",
        "relevant_courses": ["CMPUT 101", "CMPUT 174", "CMPUT 201"],
        "category": "easy_courses",
        "expected_difficulty_range": None,
        "expected_gpa_range": [3.0, 4.0],
    },
    # Category 2: Prerequisite Planning (10 queries)
    {
        "query": "what should I take after CMPUT 272 and 274?",
        "relevant_courses": ["CMPUT 301", "CMPUT 304", "CMPUT 325", "CMPUT 350"],
        "category": "prereq_planning",
        "expected_difficulty_range": None,
        "expected_gpa_range": None,
    },
    {
        "query": "prerequisites for CMPUT 404",
        "relevant_courses": ["CMPUT 301", "CMPUT 291"],
        "category": "prereq_planning",
        "expected_difficulty_range": None,
        "expected_gpa_range": None,
    },
    {
        "query": "path from 200 to 400 level AI courses",
        "relevant_courses": [
            "CMPUT 272",
            "CMPUT 274",
            "CMPUT 304",
            "CMPUT 366",
            "CMPUT 412",
        ],
        "category": "prereq_planning",
        "expected_difficulty_range": None,
        "expected_gpa_range": None,
    },
    {
        "query": "courses needed before CMPUT 350",
        "relevant_courses": ["CMPUT 272", "CMPUT 274", "CMPUT 201"],
        "category": "prereq_planning",
        "expected_difficulty_range": None,
        "expected_gpa_range": None,
    },
    {
        "query": "what to take after completing CMPUT 174 and 175",
        "relevant_courses": [
            "CMPUT 201",
            "CMPUT 204",
            "CMPUT 272",
            "CMPUT 274",
        ],
        "category": "prereq_planning",
        "expected_difficulty_range": None,
        "expected_gpa_range": None,
    },
    {
        "query": "course sequence for software engineering",
        "relevant_courses": [
            "CMPUT 174",
            "CMPUT 175",
            "CMPUT 201",
            "CMPUT 301",
            "CMPUT 404",
        ],
        "category": "prereq_planning",
        "expected_difficulty_range": None,
        "expected_gpa_range": None,
    },
    {
        "query": "prerequisites for machine learning courses",
        "relevant_courses": ["CMPUT 272", "CMPUT 274", "CMPUT 304", "MATH 125"],
        "category": "prereq_planning",
        "expected_difficulty_range": None,
        "expected_gpa_range": None,
    },
    {
        "query": "courses to prepare for CMPUT 455",
        "relevant_courses": ["CMPUT 272", "CMPUT 274", "CMPUT 304"],
        "category": "prereq_planning",
        "expected_difficulty_range": None,
        "expected_gpa_range": None,
    },
    {
        "query": "what comes after data structures",
        "relevant_courses": ["CMPUT 304", "CMPUT 325", "CMPUT 350", "CMPUT 366"],
        "category": "prereq_planning",
        "expected_difficulty_range": None,
        "expected_gpa_range": None,
    },
    {
        "query": "prerequisites for advanced algorithms",
        "relevant_courses": ["CMPUT 272", "CMPUT 274", "CMPUT 204"],
        "category": "prereq_planning",
        "expected_difficulty_range": None,
        "expected_gpa_range": None,
    },
    # Category 3: Specialization Paths (10 queries)
    {
        "query": "machine learning courses",
        "relevant_courses": [
            "CMPUT 304",
            "CMPUT 366",
            "CMPUT 412",
            "CMPUT 466",
        ],
        "category": "specialization",
        "expected_difficulty_range": None,
        "expected_gpa_range": None,
    },
    {
        "query": "courses for software engineering specialization",
        "relevant_courses": [
            "CMPUT 301",
            "CMPUT 302",
            "CMPUT 401",
            "CMPUT 404",
        ],
        "category": "specialization",
        "expected_difficulty_range": None,
        "expected_gpa_range": None,
    },
    {
        "query": "database and systems courses",
        "relevant_courses": [
            "CMPUT 291",
            "CMPUT 391",
            "CMPUT 301",
            "CMPUT 379",
        ],
        "category": "specialization",
        "expected_difficulty_range": None,
        "expected_gpa_range": None,
    },
    {
        "query": "web development courses",
        "relevant_courses": ["CMPUT 404", "CMPUT 291", "CMPUT 301"],
        "category": "specialization",
        "expected_difficulty_range": None,
        "expected_gpa_range": None,
    },
    {
        "query": "courses for game development",
        "relevant_courses": ["CMPUT 250", "CMPUT 350", "CMPUT 454"],
        "category": "specialization",
        "expected_difficulty_range": None,
        "expected_gpa_range": None,
    },
    {
        "query": "artificial intelligence specialization",
        "relevant_courses": [
            "CMPUT 304",
            "CMPUT 366",
            "CMPUT 412",
            "CMPUT 455",
        ],
        "category": "specialization",
        "expected_difficulty_range": None,
        "expected_gpa_range": None,
    },
    {
        "query": "theory and algorithms courses",
        "relevant_courses": [
            "CMPUT 272",
            "CMPUT 274",
            "CMPUT 304",
            "CMPUT 325",
        ],
        "category": "specialization",
        "expected_difficulty_range": None,
        "expected_gpa_range": None,
    },
    {
        "query": "cybersecurity courses",
        "relevant_courses": ["CMPUT 302", "CMPUT 402", "CMPUT 313"],
        "category": "specialization",
        "expected_difficulty_range": None,
        "expected_gpa_range": None,
    },
    {
        "query": "mobile app development",
        "relevant_courses": ["CMPUT 301", "CMPUT 401"],
        "category": "specialization",
        "expected_difficulty_range": None,
        "expected_gpa_range": None,
    },
    {
        "query": "computer graphics and visualization",
        "relevant_courses": ["CMPUT 250", "CMPUT 350", "CMPUT 454"],
        "category": "specialization",
        "expected_difficulty_range": None,
        "expected_gpa_range": None,
    },
    # Category 4: Professor-Specific (10 queries)
    {
        "query": "highly rated professor courses",
        "relevant_courses": ["CMPUT 174", "CMPUT 272", "CMPUT 301"],
        "category": "professor",
        "expected_difficulty_range": None,
        "expected_gpa_range": [3.0, 4.0],
    },
    {
        "query": "avoid difficult professors",
        "relevant_courses": ["CMPUT 101", "CMPUT 174", "CMPUT 201"],
        "category": "professor",
        "expected_difficulty_range": [1.0, 2.5],
        "expected_gpa_range": None,
    },
    {
        "query": "best instructors for theory courses",
        "relevant_courses": ["CMPUT 272", "CMPUT 274", "CMPUT 304"],
        "category": "professor",
        "expected_difficulty_range": None,
        "expected_gpa_range": None,
    },
    {
        "query": "courses with good teaching quality",
        "relevant_courses": [
            "CMPUT 174",
            "CMPUT 175",
            "CMPUT 272",
            "CMPUT 301",
        ],
        "category": "professor",
        "expected_difficulty_range": None,
        "expected_gpa_range": [2.8, 4.0],
    },
    {
        "query": "professors known for clear explanations",
        "relevant_courses": ["CMPUT 174", "CMPUT 272", "CMPUT 301"],
        "category": "professor",
        "expected_difficulty_range": None,
        "expected_gpa_range": None,
    },
    {
        "query": "courses with engaging lectures",
        "relevant_courses": ["CMPUT 174", "CMPUT 250", "CMPUT 272"],
        "category": "professor",
        "expected_difficulty_range": None,
        "expected_gpa_range": None,
    },
    {
        "query": "well-taught programming courses",
        "relevant_courses": ["CMPUT 174", "CMPUT 175", "CMPUT 201", "CMPUT 301"],
        "category": "professor",
        "expected_difficulty_range": None,
        "expected_gpa_range": None,
    },
    {
        "query": "courses with helpful instructors",
        "relevant_courses": ["CMPUT 174", "CMPUT 272", "CMPUT 301"],
        "category": "professor",
        "expected_difficulty_range": None,
        "expected_gpa_range": None,
    },
    {
        "query": "courses with fair grading",
        "relevant_courses": ["CMPUT 174", "CMPUT 201", "CMPUT 301"],
        "category": "professor",
        "expected_difficulty_range": None,
        "expected_gpa_range": [3.0, 4.0],
    },
    {
        "query": "instructors who care about student learning",
        "relevant_courses": ["CMPUT 174", "CMPUT 272", "CMPUT 301"],
        "category": "professor",
        "expected_difficulty_range": None,
        "expected_gpa_range": None,
    },
]


def generate_golden_queries() -> List[Dict]:
    """
    Generate golden dataset with test queries and labeled relevant courses.

    Returns:
        List of golden query dictionaries
    """
    print(f"Generated {len(GOLDEN_QUERIES)} golden queries")
    print("\nBreakdown by category:")

    categories = {}
    for query in GOLDEN_QUERIES:
        cat = query["category"]
        categories[cat] = categories.get(cat, 0) + 1

    for cat, count in categories.items():
        print(f"  {cat}: {count} queries")

    return GOLDEN_QUERIES


def save_golden_dataset(output_path: str = "apps/api/fixtures/golden-queries.json"):
    """
    Save golden dataset to JSON file.

    Args:
        output_path: Path to output JSON file
    """
    queries = generate_golden_queries()

    # Ensure directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Save to JSON
    with open(output_file, "w") as f:
        json.dump(queries, f, indent=2)

    print(f"\nGolden dataset saved to: {output_path}")
    print(f"Total queries: {len(queries)}")


if __name__ == "__main__":
    save_golden_dataset()
