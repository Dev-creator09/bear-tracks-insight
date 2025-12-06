"""
Evaluation Harness for Course Search

This module provides comprehensive evaluation of the course search system
using a golden dataset of labeled queries.

Metrics:
- Recall@10: Fraction of relevant courses in top 10 results
- MRR (Mean Reciprocal Rank): 1 / rank of first relevant course
- Precision@10: Fraction of top 10 that are relevant
- NDCG@10: Normalized Discounted Cumulative Gain

Usage:
    python -m app.evals.eval_runner

Results are stored in SQLite for historical tracking and comparison.
"""

import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog
from pydantic import BaseModel, Field

from app.services.rag import CourseSearchService
from app.config import settings

logger = structlog.get_logger()


class GoldenQuery(BaseModel):
    """Golden dataset test case"""

    query: str
    relevant_courses: List[str] = Field(
        description="Course codes that are relevant to the query"
    )
    category: str = Field(
        description="Category: easy_courses, prereq_planning, specialization, professor"
    )
    expected_difficulty_range: Optional[List[float]] = None
    expected_gpa_range: Optional[List[float]] = None


class EvalResult(BaseModel):
    """Evaluation result for a single test case"""

    query: str
    category: str
    recall_at_10: float
    mrr: float
    precision_at_10: float
    ndcg_at_10: float
    latency_ms: int
    cost_usd: float
    retrieved_courses: List[str]
    relevant_courses: List[str]


class AggregateMetrics(BaseModel):
    """Aggregated evaluation metrics"""

    recall_at_10: float
    mrr: float
    precision_at_10: float
    ndcg_at_10: float
    avg_latency_ms: int
    total_cost_usd: float
    num_queries: int


class EvalRunner:
    """
    Evaluation harness for course search system.

    Runs test queries from golden dataset and computes retrieval metrics.
    Compares against baseline and stores results in SQLite database.
    """

    def __init__(
        self,
        search_service: CourseSearchService,
        golden_dataset_path: str = "apps/api/fixtures/golden-queries.json",
        baseline_path: str = "apps/api/evals/baseline.json",
        db_path: str = "apps/api/evals/evals.db",
    ):
        """
        Initialize the evaluation runner.

        Args:
            search_service: Configured CourseSearchService instance
            golden_dataset_path: Path to golden queries JSON file
            baseline_path: Path to baseline results JSON
            db_path: Path to SQLite database for storing results
        """
        self.search_service = search_service
        self.golden_dataset_path = Path(golden_dataset_path)
        self.baseline_path = Path(baseline_path)
        self.db_path = Path(db_path)
        self.log = logger.bind(service="eval_runner")

        # Initialize database
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database for storing evaluation results."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create eval_runs table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS eval_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                model_version TEXT,
                overall_recall REAL,
                overall_mrr REAL,
                overall_precision REAL,
                overall_ndcg REAL,
                total_cost_usd REAL,
                avg_latency_ms INTEGER,
                num_queries INTEGER
            )
        """
        )

        # Create eval_test_cases table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS eval_test_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                query TEXT NOT NULL,
                category TEXT,
                recall_at_10 REAL,
                mrr REAL,
                precision_at_10 REAL,
                ndcg_at_10 REAL,
                latency_ms INTEGER,
                cost_usd REAL,
                retrieved_courses TEXT,
                relevant_courses TEXT,
                FOREIGN KEY (run_id) REFERENCES eval_runs (id)
            )
        """
        )

        conn.commit()
        conn.close()

        self.log.info("eval_db_initialized", db_path=str(self.db_path))

    def load_golden_dataset(self) -> List[GoldenQuery]:
        """
        Load golden dataset from JSON file.

        Returns:
            List of GoldenQuery test cases

        Raises:
            FileNotFoundError: If golden dataset file doesn't exist
            ValidationError: If dataset format is invalid
        """
        if not self.golden_dataset_path.exists():
            raise FileNotFoundError(
                f"Golden dataset not found: {self.golden_dataset_path}"
            )

        with open(self.golden_dataset_path, "r") as f:
            data = json.load(f)

        queries = [GoldenQuery(**item) for item in data]

        self.log.info(
            "golden_dataset_loaded",
            num_queries=len(queries),
            categories=list(set(q.category for q in queries)),
        )

        return queries

    def _calculate_recall_at_k(
        self, retrieved: List[str], relevant: List[str], k: int = 10
    ) -> float:
        """
        Calculate Recall@k: fraction of relevant items in top k results.

        Args:
            retrieved: List of retrieved course codes
            relevant: List of relevant course codes
            k: Cutoff position

        Returns:
            Recall@k score between 0 and 1
        """
        if not relevant:
            return 0.0

        retrieved_k = set(retrieved[:k])
        relevant_set = set(relevant)

        hits = len(retrieved_k & relevant_set)
        return hits / len(relevant_set)

    def _calculate_mrr(self, retrieved: List[str], relevant: List[str]) -> float:
        """
        Calculate Mean Reciprocal Rank: 1 / rank of first relevant item.

        Args:
            retrieved: List of retrieved course codes
            relevant: List of relevant course codes

        Returns:
            MRR score between 0 and 1
        """
        relevant_set = set(relevant)

        for i, course_code in enumerate(retrieved, 1):
            if course_code in relevant_set:
                return 1.0 / i

        return 0.0

    def _calculate_precision_at_k(
        self, retrieved: List[str], relevant: List[str], k: int = 10
    ) -> float:
        """
        Calculate Precision@k: fraction of top k that are relevant.

        Args:
            retrieved: List of retrieved course codes
            relevant: List of relevant course codes
            k: Cutoff position

        Returns:
            Precision@k score between 0 and 1
        """
        if not retrieved[:k]:
            return 0.0

        retrieved_k = retrieved[:k]
        relevant_set = set(relevant)

        hits = sum(1 for code in retrieved_k if code in relevant_set)
        return hits / len(retrieved_k)

    def _calculate_dcg(self, retrieved: List[str], relevant: List[str], k: int = 10) -> float:
        """
        Calculate Discounted Cumulative Gain.

        Args:
            retrieved: List of retrieved course codes
            relevant: List of relevant course codes
            k: Cutoff position

        Returns:
            DCG score
        """
        relevant_set = set(relevant)
        dcg = 0.0

        for i, course_code in enumerate(retrieved[:k], 1):
            if course_code in relevant_set:
                # Binary relevance: rel = 1 if relevant, 0 otherwise
                dcg += 1.0 / (i + 1).bit_length()  # log2(i + 1)

        return dcg

    def _calculate_ndcg_at_k(
        self, retrieved: List[str], relevant: List[str], k: int = 10
    ) -> float:
        """
        Calculate Normalized Discounted Cumulative Gain@k.

        Args:
            retrieved: List of retrieved course codes
            relevant: List of relevant course codes
            k: Cutoff position

        Returns:
            NDCG@k score between 0 and 1
        """
        dcg = self._calculate_dcg(retrieved, relevant, k)

        # Ideal DCG: all relevant items at the top
        ideal_retrieved = relevant[:k]
        idcg = self._calculate_dcg(ideal_retrieved, relevant, k)

        if idcg == 0:
            return 0.0

        return dcg / idcg

    async def run_single_eval(self, test_case: GoldenQuery) -> EvalResult:
        """
        Run evaluation for a single test case.

        Args:
            test_case: Golden query test case

        Returns:
            EvalResult with metrics
        """
        start_time = time.time()

        # Execute search
        search_result = await self.search_service.search(
            query=test_case.query,
            limit=10,
        )

        latency_ms = int((time.time() - start_time) * 1000)

        # Extract retrieved course codes
        retrieved_courses = [
            f"{course['subject']} {course['number']}"
            for course in search_result["results"]
        ]

        # Calculate metrics
        recall = self._calculate_recall_at_k(
            retrieved_courses, test_case.relevant_courses, k=10
        )
        mrr = self._calculate_mrr(retrieved_courses, test_case.relevant_courses)
        precision = self._calculate_precision_at_k(
            retrieved_courses, test_case.relevant_courses, k=10
        )
        ndcg = self._calculate_ndcg_at_k(
            retrieved_courses, test_case.relevant_courses, k=10
        )

        result = EvalResult(
            query=test_case.query,
            category=test_case.category,
            recall_at_10=recall,
            mrr=mrr,
            precision_at_10=precision,
            ndcg_at_10=ndcg,
            latency_ms=latency_ms,
            cost_usd=search_result.get("cost_usd", 0.0),
            retrieved_courses=retrieved_courses,
            relevant_courses=test_case.relevant_courses,
        )

        self.log.info(
            "eval_case_completed",
            query=test_case.query[:50],
            category=test_case.category,
            recall=recall,
            mrr=mrr,
            latency_ms=latency_ms,
        )

        return result

    def _aggregate_metrics(self, results: List[EvalResult]) -> AggregateMetrics:
        """
        Aggregate metrics across all test cases.

        Args:
            results: List of individual eval results

        Returns:
            AggregateMetrics with averaged scores
        """
        if not results:
            return AggregateMetrics(
                recall_at_10=0.0,
                mrr=0.0,
                precision_at_10=0.0,
                ndcg_at_10=0.0,
                avg_latency_ms=0,
                total_cost_usd=0.0,
                num_queries=0,
            )

        return AggregateMetrics(
            recall_at_10=sum(r.recall_at_10 for r in results) / len(results),
            mrr=sum(r.mrr for r in results) / len(results),
            precision_at_10=sum(r.precision_at_10 for r in results) / len(results),
            ndcg_at_10=sum(r.ndcg_at_10 for r in results) / len(results),
            avg_latency_ms=int(sum(r.latency_ms for r in results) / len(results)),
            total_cost_usd=sum(r.cost_usd for r in results),
            num_queries=len(results),
        )

    def _aggregate_by_category(
        self, results: List[EvalResult]
    ) -> Dict[str, AggregateMetrics]:
        """
        Aggregate metrics by category.

        Args:
            results: List of individual eval results

        Returns:
            Dict mapping category to aggregate metrics
        """
        by_category = {}

        for category in set(r.category for r in results):
            category_results = [r for r in results if r.category == category]
            by_category[category] = self._aggregate_metrics(category_results)

        return by_category

    def _load_baseline(self) -> Optional[Dict[str, Any]]:
        """
        Load baseline results from JSON file.

        Returns:
            Baseline results dict or None if file doesn't exist
        """
        if not self.baseline_path.exists():
            self.log.warning("baseline_not_found", path=str(self.baseline_path))
            return None

        with open(self.baseline_path, "r") as f:
            baseline = json.load(f)

        self.log.info("baseline_loaded", path=str(self.baseline_path))
        return baseline

    async def run_full_eval(self) -> Dict[str, Any]:
        """
        Run full evaluation on entire golden dataset.

        Returns:
            Dict with overall metrics, by-category metrics, and comparison to baseline
        """
        self.log.info("full_eval_started")

        # Load golden dataset
        test_cases = self.load_golden_dataset()

        # Run evaluations
        results = []
        for test_case in test_cases:
            result = await self.run_single_eval(test_case)
            results.append(result)

        # Aggregate metrics
        overall_metrics = self._aggregate_metrics(results)
        by_category = self._aggregate_by_category(results)

        # Load baseline and compare
        baseline = self._load_baseline()
        comparison = {}

        if baseline and "overall" in baseline:
            baseline_overall = baseline["overall"]
            comparison = {
                "recall_delta": overall_metrics.recall_at_10
                - baseline_overall.get("recall_at_10", 0),
                "mrr_delta": overall_metrics.mrr - baseline_overall.get("mrr", 0),
                "cost_delta": overall_metrics.total_cost_usd
                - baseline_overall.get("total_cost_usd", 0),
            }

        # Prepare results
        eval_results = {
            "overall": overall_metrics.model_dump(),
            "by_category": {
                cat: metrics.model_dump() for cat, metrics in by_category.items()
            },
            "comparison_to_baseline": comparison,
            "test_cases": [r.model_dump() for r in results],
            "timestamp": datetime.utcnow().isoformat(),
            "model_version": "claude-3-5-sonnet-20241022",
        }

        # Save to database
        self._save_results(eval_results)

        self.log.info(
            "full_eval_completed",
            overall_recall=overall_metrics.recall_at_10,
            overall_mrr=overall_metrics.mrr,
            total_cost=overall_metrics.total_cost_usd,
        )

        return eval_results

    def _save_results(self, results: Dict[str, Any]):
        """
        Save evaluation results to SQLite database.

        Args:
            results: Full evaluation results dict
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        overall = results["overall"]

        # Insert eval run
        cursor.execute(
            """
            INSERT INTO eval_runs (
                timestamp, model_version, overall_recall, overall_mrr,
                overall_precision, overall_ndcg, total_cost_usd, avg_latency_ms, num_queries
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                results["timestamp"],
                results["model_version"],
                overall["recall_at_10"],
                overall["mrr"],
                overall["precision_at_10"],
                overall["ndcg_at_10"],
                overall["total_cost_usd"],
                overall["avg_latency_ms"],
                overall["num_queries"],
            ),
        )

        run_id = cursor.lastrowid

        # Insert test cases
        for test_case in results["test_cases"]:
            cursor.execute(
                """
                INSERT INTO eval_test_cases (
                    run_id, query, category, recall_at_10, mrr, precision_at_10,
                    ndcg_at_10, latency_ms, cost_usd, retrieved_courses, relevant_courses
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    run_id,
                    test_case["query"],
                    test_case["category"],
                    test_case["recall_at_10"],
                    test_case["mrr"],
                    test_case["precision_at_10"],
                    test_case["ndcg_at_10"],
                    test_case["latency_ms"],
                    test_case["cost_usd"],
                    json.dumps(test_case["retrieved_courses"]),
                    json.dumps(test_case["relevant_courses"]),
                ),
            )

        conn.commit()
        conn.close()

        self.log.info("eval_results_saved", run_id=run_id, db_path=str(self.db_path))

    def get_recent_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent evaluation runs from database.

        Args:
            limit: Number of runs to retrieve

        Returns:
            List of eval run records
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM eval_runs
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (limit,),
        )

        runs = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return runs


# CLI entry point
async def main():
    """Run evaluation from command line."""
    from app.database import get_db
    from redis.asyncio import Redis

    # Initialize dependencies
    db = await anext(get_db())
    redis_client = Redis.from_url(settings.redis_url)

    # Create search service
    search_service = CourseSearchService(db, redis_client)

    # Create eval runner
    runner = EvalRunner(search_service)

    # Run evaluation
    results = await runner.run_full_eval()

    # Print results
    print("\n" + "=" * 80)
    print("EVALUATION RESULTS")
    print("=" * 80)
    print(f"\nOverall Metrics:")
    print(f"  Recall@10:     {results['overall']['recall_at_10']:.3f}")
    print(f"  MRR:           {results['overall']['mrr']:.3f}")
    print(f"  Precision@10:  {results['overall']['precision_at_10']:.3f}")
    print(f"  NDCG@10:       {results['overall']['ndcg_at_10']:.3f}")
    print(f"  Avg Latency:   {results['overall']['avg_latency_ms']}ms")
    print(f"  Total Cost:    ${results['overall']['total_cost_usd']:.2f}")

    print(f"\nBy Category:")
    for category, metrics in results["by_category"].items():
        print(f"\n  {category}:")
        print(f"    Recall@10: {metrics['recall_at_10']:.3f}")
        print(f"    MRR:       {metrics['mrr']:.3f}")

    if results["comparison_to_baseline"]:
        print(f"\nComparison to Baseline:")
        comp = results["comparison_to_baseline"]
        print(f"  Recall Δ:  {comp['recall_delta']:+.3f}")
        print(f"  MRR Δ:     {comp['mrr_delta']:+.3f}")
        print(f"  Cost Δ:    ${comp['cost_delta']:+.2f}")

    print("\n" + "=" * 80)

    await redis_client.close()
    await db.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
