"""
Evaluation endpoints

Provides API endpoints for running and viewing search evaluation results.
Admin-only endpoints requiring API key authentication.
"""

import structlog
from fastapi import APIRouter, HTTPException, Header, Depends
from redis.asyncio import Redis
from typing import Optional, Dict, Any

from app.dependencies import DbSession
from app.services.rag import CourseSearchService
from app.evals.eval_runner import EvalRunner
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


def verify_admin_key(x_api_key: Optional[str] = Header(None)):
    """
    Verify admin API key for protected endpoints.

    Args:
        x_api_key: API key from request header

    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Provide X-API-Key header.",
        )

    # In production, use a secure key from settings
    expected_key = getattr(settings, "admin_api_key", "dev-admin-key-change-me")

    if x_api_key != expected_key:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key",
        )


@router.get("/run")
async def run_evaluation(
    db: DbSession,
    redis: Redis = Depends(get_redis),
    api_key: str = Depends(verify_admin_key),
) -> Dict[str, Any]:
    """
    Run full evaluation suite on golden dataset.

    This endpoint triggers a complete evaluation run:
    1. Loads golden dataset with labeled queries
    2. Executes search for each test case
    3. Computes retrieval metrics (Recall@10, MRR, NDCG)
    4. Compares against baseline results
    5. Stores results in SQLite database

    Requires admin API key authentication via X-API-Key header.

    Args:
        db: Database session
        redis: Redis client
        api_key: Admin API key (from header)

    Returns:
        Dict with evaluation results including:
        - overall: Aggregate metrics across all queries
        - by_category: Metrics broken down by category
        - comparison_to_baseline: Deltas vs baseline
        - test_cases: Individual results for each query

    Example:
        curl -X GET http://localhost:8000/api/v1/evals/run \\
             -H "X-API-Key: your-admin-key"
    """
    log = logger.bind(endpoint="run_evaluation")

    try:
        log.info("eval_run_started")

        # Initialize services
        search_service = CourseSearchService(db, redis)

        # Create eval runner
        runner = EvalRunner(search_service)

        # Run evaluation
        results = await runner.run_full_eval()

        log.info(
            "eval_run_completed",
            overall_recall=results["overall"]["recall_at_10"],
            overall_mrr=results["overall"]["mrr"],
            total_cost=results["overall"]["total_cost_usd"],
        )

        return results

    except FileNotFoundError as e:
        log.error("eval_dataset_not_found", error=str(e))
        raise HTTPException(
            status_code=404,
            detail="Golden dataset not found. Run generate_golden_set.py first.",
        )

    except Exception as e:
        log.error("eval_run_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation failed: {str(e)}",
        )


@router.get("/history")
async def get_eval_history(
    limit: int = 10,
    api_key: str = Depends(verify_admin_key),
) -> Dict[str, Any]:
    """
    Get recent evaluation run history.

    Returns historical evaluation runs from the database,
    allowing comparison of performance over time.

    Requires admin API key authentication via X-API-Key header.

    Args:
        limit: Number of recent runs to return (default 10)
        api_key: Admin API key (from header)

    Returns:
        Dict with list of recent evaluation runs

    Example:
        curl -X GET http://localhost:8000/api/v1/evals/history?limit=5 \\
             -H "X-API-Key: your-admin-key"
    """
    log = logger.bind(endpoint="get_eval_history")

    try:
        # Create minimal runner just to access DB
        runner = EvalRunner(
            search_service=None,  # Not needed for history
        )

        runs = runner.get_recent_runs(limit=limit)

        log.info("eval_history_retrieved", num_runs=len(runs))

        return {
            "runs": runs,
            "count": len(runs),
        }

    except Exception as e:
        log.error("eval_history_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve eval history: {str(e)}",
        )
