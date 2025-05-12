import asyncio
from app.fetch_github import run_pr_fetch
from app.pr_review_agent import review_hunk
from logging_wrapper import log_async_exceptions,log_exceptions
import logging

logger = logging.getLogger(__name__)

async def retry_once(coro_func, *args, **kwargs):
    try:
        return await coro_func(*args, **kwargs)
    except Exception as e:
        logger.warning(f"First attempt failed with: {e}. Retrying once...")
        try:
            return await coro_func(*args, **kwargs)
        except Exception as e2:
            logger.error(f"Second attempt failed with: {e2}")
            return e2  # Let the caller filter this if needed

@log_async_exceptions
async def review_pr_agents(repo_url, pr_number, token=None):
    pr_info, pr_files = await run_pr_fetch(repo_url, pr_number, token=token)
    
    review_tasks = [
        asyncio.create_task(retry_once(review_hunk, pr_info, hunk))
        for hunk in pr_files
    ]
    
    reviews = await asyncio.gather(*review_tasks, return_exceptions=True)

    successful_reviews = []
    failed_reviews = []

    for result in reviews:
        if isinstance(result, Exception):
            logger.error(f"Review task failed: {result}")
            failed_reviews.append(result)
        else:
            successful_reviews.append(result)

    if not successful_reviews:
        raise RuntimeError("All review tasks failed. No successful reviews generated.")

    return successful_reviews
