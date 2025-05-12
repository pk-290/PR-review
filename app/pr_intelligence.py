import asyncio
from app.fetch_github import run_pr_fetch
from app.pr_review_agent import review_hunk

async def review_pr_agents(repo_url, pr_number, token=None):
    pr_info , pr_files = await run_pr_fetch(repo_url, pr_number, token=None)
    review_tasks = [
        asyncio.create_task(review_hunk(pr_info, hunk))
        for hunk in pr_files
    ]
    reviews = await asyncio.gather(*review_tasks, return_exceptions=True)
    return reviews

# if __name__ == "__main__":
# #     # Example usage:
#     url = "https://github.com/potpie-ai/potpie"
#     pr_number = 398
#     final_report = asyncio.run(review_pr_agents(url,pr_number))
#     print(final_report)
