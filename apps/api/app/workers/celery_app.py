"""
Celery application configuration for Bear Tracks worker.

Configures task queues, serialization, retry policies, and routing
for distributed background job processing.
"""

from celery import Celery
from kombu import Queue

# Import settings (will create config later)
# from app.config import settings

# ============================================================================
# Celery App Initialization
# ============================================================================

celery_app = Celery(
    'bear_tracks_worker',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
    include=[
        'app.workers.tasks.scrape_course',
    ]
)

# ============================================================================
# Celery Configuration
# ============================================================================

celery_app.conf.update(
    # Serialization
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],

    # Timezone
    timezone='America/Edmonton',
    enable_utc=True,

    # Task results
    result_expires=3600,  # 1 hour
    result_persistent=True,

    # Task execution
    task_acks_late=True,  # Acknowledge after task completion (reliability)
    worker_prefetch_multiplier=1,  # One task at a time per worker
    task_reject_on_worker_lost=True,  # Re-queue if worker dies

    # Task tracking
    task_track_started=True,
    task_send_sent_event=True,

    # Worker configuration
    worker_send_task_events=True,
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks (prevent memory leaks)

    # Task routing - different queues for different priorities
    task_routes={
        'scrape_course': {'queue': 'scraping'},
        'analyze_sentiment': {'queue': 'analysis'},
        'generate_embeddings': {'queue': 'analysis'},
        'handle_failed_scrape': {'queue': 'dead_letter'},
    },

    # Default queue configuration
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',

    # Define queues
    task_queues=(
        Queue('default', routing_key='default'),
        Queue('scraping', routing_key='scraping', priority=5),
        Queue('analysis', routing_key='analysis', priority=3),
        Queue('dead_letter', routing_key='dead_letter', priority=1),
    ),

    # Retry policy defaults
    task_autoretry_for=(Exception,),
    task_max_retries=3,
    task_default_retry_delay=10,  # 10 seconds initial delay

    # Retry backoff configuration
    task_retry_backoff=True,  # Exponential backoff
    task_retry_backoff_max=600,  # Max 10 minutes between retries
    task_retry_jitter=True,  # Add randomness to avoid thundering herd

    # Logging
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',

    # Monitoring
    worker_enable_remote_control=True,

    # Performance
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
)

# ============================================================================
# Beat Schedule (for periodic tasks - future use)
# ============================================================================

celery_app.conf.beat_schedule = {
    # Example: scrape all courses daily at 2 AM
    # 'scrape-all-courses': {
    #     'task': 'scrape_all_courses',
    #     'schedule': crontab(hour=2, minute=0),
    # },
}

# ============================================================================
# Celery Signals (for hooks and monitoring)
# ============================================================================

from celery.signals import task_prerun, task_postrun, task_failure
import logging

logger = logging.getLogger(__name__)


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):
    """Log when a task starts."""
    logger.info(f"Task {task.name}[{task_id}] starting with args={args}, kwargs={kwargs}")


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, **extra):
    """Log when a task completes successfully."""
    logger.info(f"Task {task.name}[{task_id}] completed successfully")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, **extra):
    """Log when a task fails."""
    logger.error(
        f"Task {sender.name}[{task_id}] failed with exception: {exception}",
        exc_info=True
    )
