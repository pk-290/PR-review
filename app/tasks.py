import os
import time
import logging
from celery import Celery
from app.store import *
from app.parser import split_diff_by_file
from app.github import fetch_pr_diff
from app.agent import ReviewAgent
from app.linter import run_linters
from app.llm_garden import execute_chain

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

@cel.task(bind=True)         # Maximum number of retries
def analyze_pr(self, repo_url, pr_number, token):
    task_id = self.request.id
    logger.info(f"Starting PR analysis for {repo_url}#{pr_number} (Task ID: {task_id})")
    
    try:
        safe_redis_operation(init_task, task_id, repo_url, pr_number)
        safe_redis_operation(set_task_status, task_id, "processing")
            
        diff = fetch_pr_diff(repo_url, pr_number, token)
        
        # Check diff size for large PRs
        if len(diff) > 1_000_000:  # ~1MB diff
            logger.warning(f"Large diff detected ({len(diff)} bytes) for {repo_url}#{pr_number}")
            safe_redis_operation(set_task_status, task_id, "large_diff_processing")
        
        files = split_diff_by_file(diff)
        
        # Schedule per-hunk reviews
        if not files:
            logger.warning(f"No files found in diff for {repo_url}#{pr_number}")
            safe_redis_operation(set_task_status, task_id, "no_files_found")
            return
        
        for idx, f in enumerate(files):
            hunk_id = f"hunk-{idx}"
            safe_redis_operation(add_hunk, task_id, hunk_id)
            lint_and_review_hunk.delay(task_id, hunk_id, f["filename"], f["hunk"], repo_url, pr_number, token)
        
        logger.info(f"Scheduled {len(files)} hunks for analysis for task {task_id}")
        
    except Exception as e:
        logger.error(f"Error in analyze_pr task: {e}", exc_info=True)
        safe_redis_operation(set_task_status, task_id, "error")
        self.retry(exc=e, countdown=60)  # Retry after 60 seconds

@cel.task(bind=True)         # Maximum number of retries
def lint_and_review_hunk(self, task_id, hunk_id, filename, hunk, repo_url, pr_number, token):
    logger.info(f"Processing hunk {hunk_id} for task {task_id}")
    
    try:
        # Run linters
        lint_warnings = run_linters(filename, hunk)
        
        # LLM call for hunk
        prompt_template = """
        Code hunk from {filename}:
        {hunk}
        Linter warnings:
        {lint_warnings}
        Suggest style, bug fixes, performance improvements.
        """
        input_vars = {"filename": filename, "hunk": hunk, "lint_warnings": lint_warnings}
        llm_comments = execute_chain(prompt_template, input_vars)
        result = {
            "filename": filename, 
            "hunk_id": hunk_id, 
            "lint": lint_warnings, 
            "comments": llm_comments
        }
        
        safe_redis_operation(set_hunk_result, task_id, hunk_id, result)

        # Check if this is the last hunk to complete
        all_hunks = safe_redis_operation(get_all_hunk_results, task_id)

        logger.info("all hunk successfull...")

        expected_hunks = safe_redis_operation(
            lambda: len(r.lrange(f"task:{task_id}:hunks", 0, -1))
        )
        
        # Use a Redis transaction to ensure atomicity
        if len(all_hunks) == expected_hunks:
            # Use Redis to flag that synthesis should start
            with r.pipeline() as pipe:
                try:
                    # Watch the key to ensure no other process modifies it
                    pipe.watch(f"task:{task_id}:synthesis_started")
                    
                    # Check if synthesis has already been triggered
                    if not pipe.get(f"task:{task_id}:synthesis_started"):
                        # Start a transaction
                        pipe.multi()
                        # Mark synthesis as started
                        pipe.set(f"task:{task_id}:synthesis_started", "1")
                        pipe.execute()
                        
                        # Trigger the synthesis
                        logger.info(f"All hunks processed for task {task_id}, starting synthesis")
                        ReviewAgent(task_id, repo_url, pr_number, token).synthesize_and_post()
                    
                except Exception as e:
                    logger.error(f"Error triggering synthesis: {e}")
                    pipe.reset()
        
    except Exception as e:
        logger.error(f"Error processing hunk {hunk_id}: {e}", exc_info=True)
        self.retry(exc=e)
