import os
import time
import logging
from celery import Celery
from app.store import *
import asyncio
from app.pr_intelligence import review_pr_agents

# Set up logging
logger = logging.getLogger(__name__)

# Environment variables with defaults
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_BACKEND_URL = os.environ.get('CELERY_BACKEND_URL','redis://redis:6379/0')

# Initialize Celery
cel = Celery(__name__, broker=CELERY_BROKER_URL, backend=CELERY_BACKEND_URL)

# Celery configuration
cel.conf.update(
    broker_connection_timeout=10,
    broker_connection_max_retries=5,
    result_backend_always_retry=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    enable_utc=True,
)

# Windows-specific configuration
if os.name == 'nt':  # Windows
    cel.conf.update(
        broker_connection_retry_on_startup=True,
        worker_pool_restarts=True,
        worker_cancel_long_running_tasks_on_connection_loss=True,
    )

def safe_redis_operation(operation, *args, **kwargs):
    """Wrapper for Redis operations with error handling"""
    max_retries = 2
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            return operation(*args, **kwargs)
        except Exception as e:
            retry_count += 1
            logger.warning(f"Redis operation failed (attempt {retry_count}): {e}")
            if retry_count >= max_retries:
                logger.error(f"Redis operation failed after {max_retries} attempts")
                raise
            time.sleep(1)  # Wait before retrying

@cel.task(bind=True)
def analyze_pr(self,repo_url,pr_number,github_token):
    set_task_status(self.request.id, "processing")
    try:
        reviews  =  asyncio.run(review_pr_agents(repo_url,pr_number,github_token))
        logger.info("Finished agents, got %d reviews", len(reviews))
        set_final_result(self.request.id,reviews)
        return reviews
    except Exception as e:
        set_task_status(self.request.id, "failed")
        raise e

