import requests
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def fetch_pr_diff(repo_url: str, pr_number: int, token: str) -> str:
    # call GitHub API: GET /repos/:owner/:repo/pulls/:pr_number with Accept: diff
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3.diff"}
    resp = requests.get(f"{repo_url}/pull/{pr_number}.diff", headers=headers)
    # resp = requests.get("https://patch-diff.githubusercontent.com/raw/potpie-ai/potpie/pull/396.diff", headers=headers)
    # print("="*50)
    print(resp.text[500:])
    return resp.text
