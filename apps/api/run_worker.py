#!/usr/bin/env python3
"""
Celery worker startup script for Bear Tracks.

This script starts the Celery worker with optimized settings for
production use including concurrency, task limits, and monitoring.

Usage:
    python run_worker.py

Environment Variables:
    REDIS_URL: Redis connection URL (default: redis://localhost:6379/0)
    WORKER_CONCURRENCY: Number of concurrent workers (default: 10)
    WORKER_LOG_LEVEL: Logging level (default: info)
"""

import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.workers.celery_app import celery_app

if __name__ == '__main__':
    # Worker configuration
    worker_args = [
        'worker',

        # Logging
        f'--loglevel={os.getenv("WORKER_LOG_LEVEL", "info")}',

        # Concurrency
        f'--concurrency={os.getenv("WORKER_CONCURRENCY", "10")}',

        # Task limits (restart worker after 100 tasks to prevent memory leaks)
        '--max-tasks-per-child=100',

        # Monitoring
        '--task-events',  # Send task events for monitoring

        # Performance optimizations
        '--without-gossip',  # Disable gossip protocol (saves bandwidth)
        '--without-mingle',  # Don't sync with other workers at startup
        '--without-heartbeat',  # Disable heartbeat (managed by supervisor)

        # Pool
        '--pool=prefork',  # Use prefork pool (multiprocessing)

        # Queues (process all queues)
        '--queues=default,scraping,analysis,dead_letter',
    ]

    print("=" * 70)
    print("Starting Bear Tracks Celery Worker")
    print("=" * 70)
    print(f"Concurrency: {os.getenv('WORKER_CONCURRENCY', '10')}")
    print(f"Log Level: {os.getenv('WORKER_LOG_LEVEL', 'info')}")
    print(f"Redis URL: {os.getenv('REDIS_URL', 'redis://localhost:6379/0')}")
    print(f"Queues: default, scraping, analysis, dead_letter")
    print("=" * 70)

    celery_app.worker_main(worker_args)
