import requests
import os
import re
import base64
import json
import aiohttp
import asyncio
import base64
from logging_wrapper import log_async_exceptions,log_exceptions

# GitHub API base URL
API_URL = "https://api.github.com"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

@log_exceptions
def parse_repo_url(url):
    """Parses GitHub URL to extract owner and repo name."""
    match = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?$", url)
    if not match:
        match = re.match(r"git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$", url)
    if match:
        return match.group(1), match.group(2)
    else:
        raise ValueError(f"Invalid GitHub repository URL: {url}")


def get_github_headers(token):
    """Returns headers for GitHub API requests."""
    if not token:
        raise ValueError("GitHub token is missing. Provide it as argument or set GITHUB_TOKEN environment variable.")
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

def format_pr_details_to_text(pr_data):
    """Formats PR JSON data into a human-readable text string."""
    details = []
    details.append(f"--- Pull Request Details ---")
    details.append(f"Title: {pr_data.get('title', 'N/A')}")
    details.append(f"Number: #{pr_data.get('number', 'N/A')}")
    details.append(f"State: {pr_data.get('state', 'N/A').capitalize()}")
    details.append(f"Author: {pr_data.get('user', {}).get('login', 'N/A')}")
    details.append(f"URL: {pr_data.get('html_url', 'N/A')}")

    details.append("\n--- Branches ---")
    head = pr_data.get('head', {})
    base = pr_data.get('base', {})
    details.append(f"Source (Head): {head.get('label', 'N/A')} (Ref: {head.get('ref', 'N/A')}, SHA: {head.get('sha', 'N/A')})")
    details.append(f"Target (Base): {base.get('label', 'N/A')} (Ref: {base.get('ref', 'N/A')}, SHA: {base.get('sha', 'N/A')})")

    details.append("\n--- Contributions ---")
    details.append(f"Commits: {pr_data.get('commits', 'N/A')}")
    details.append(f"Files Changed: {pr_data.get('changed_files', 'N/A')}")
    details.append(f"Additions: +{pr_data.get('additions', 'N/A')}")
    details.append(f"Deletions: -{pr_data.get('deletions', 'N/A')}")

    labels = pr_data.get('labels', [])
    if labels:
        label_names = [label.get('name', 'Unknown Label') for label in labels]
        details.append(f"Labels: {', '.join(label_names)}")
    else:
        details.append("Labels: None")

    assignees = pr_data.get('assignees', [])
    if assignees:
        assignee_logins = [assignee.get('login', 'Unknown Assignee') for assignee in assignees]
        details.append(f"Assignees: {', '.join(assignee_logins)}")
    else:
        details.append("Assignees: None")

    requested_reviewers = pr_data.get('requested_reviewers', [])
    if requested_reviewers:
        reviewer_logins = [r.get('login', 'Unknown Reviewer') for r in requested_reviewers]
        details.append(f"Requested Reviewers: {', '.join(reviewer_logins)}")
    else:
        details.append("Requested Reviewers: None")
    
    milestone = pr_data.get('milestone')
    if milestone:
        details.append(f"Milestone: {milestone.get('title', 'N/A')}")
    else:
        details.append("Milestone: None")

    body = pr_data.get('body')
    details.append("\n--- PR Body/Description ---")
    if body and body.strip():
        details.append(body)
    else:
        details.append("(No description provided)")
    return "\n".join(details)

@log_async_exceptions   
async def fetch_pr_details(owner, repo, pr_number, token):
    """Asynchronously fetches PR details and returns formatted text and raw JSON."""

    url = f"{API_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = get_github_headers(token)

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"GitHub API Error: {resp.status} {text}")
            data = await resp.json()
            return format_pr_details_to_text(data), data

@log_async_exceptions
async def fetch_pr_files(owner: str, repo: str, pr_number: int, token: str) -> list:
    """
    Fetch the list of files in a PR, paging concurrently.
    """
    url = f"{API_URL}/repos/{owner}/{repo}/pulls/{pr_number}/files"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        # 1) First request to get page count from Link header
        async with session.get(f"{url}?per_page=100&page=1") as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"GitHub API Error: {resp.status} {text}")
            first_page = await resp.json()
            link = resp.headers.get("Link", "")
            
        # 2) Parse total number of pages from 'Link' header, if present
        last_page = 1
        match = re.search(r'<[^>]+[&?]page=(\d+)>; rel="last"', link)
        if match:
            last_page = int(match.group(1))

        # 3) If there's more than one page, fetch the rest concurrently
        tasks = []
        for page in range(2, last_page + 1):
            tasks.append(session.get(f"{url}?per_page=100&page={page}"))

        results = []
        if tasks:
            responses = await asyncio.gather(*tasks)
            for resp in responses:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"GitHub API Error: {resp.status} {text}")
                results.extend(await resp.json())

        # Combine first page + the rest
        return first_page + results

@log_async_exceptions
async def fetch_file_content(owner: str, repo: str, file_path: str, ref: str, token: str) -> str:
    """Asynchronously fetches the content of a specific file at a given ref."""
    url = f"{API_URL}/repos/{owner}/{repo}/contents/{file_path}?ref={ref}"
    headers = get_github_headers(token)
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            content_data = await resp.json()
        
        # If GitHub returns base64‐encoded content
        if content_data.get("encoding") == "base64":
            raw = content_data.get("content") or ""
            return base64.b64decode(raw).decode("utf-8", errors="replace")
        
        # Fallback to download_url if provided
        download_url = content_data.get("download_url")
        if download_url:
            async with session.get(download_url) as dl_resp:
                dl_resp.raise_for_status()
                return await dl_resp.text()
        
        # Sometimes content is inline but not base64
        if "content" in content_data:
            return content_data["content"]
        
        # Empty file case
        if content_data.get("type") == "file" and content_data.get("size") == 0:
            return ""
        
        # Last resort: error message
        file_type = content_data.get("type", "N/A")
        file_size = content_data.get("size", "N/A")
        return (f"Could not decode/retrieve content for {file_path}. "
                f"Type: {file_type}, Size: {file_size}")


def format_file_content(content,filename):
    """Fetches and formats a single file's content with line numbers."""
    # Fetch content
    # content = await fetch_file_content(owner, repo, filename, ref, token)
    if not content:
        return f"--- Content for: {filename} ---\n(File is empty or only whitespace)"
    lines = content.splitlines()
    max_width = len(str(len(lines)))
    buf = [f"--- Content for: {filename} ---"]
    for i, line in enumerate(lines, 1):
        buf.append(f"{i:{max_width}d}: {line}")
    return "\n".join(buf)


@log_async_exceptions
async def run_pr_fetch(repo_url, pr_number, token=None):
    """
    Fetch PR details and file contents. 
    Inputs: repo_url, pull request number, and GitHub token.
    Returns: (pr_details_text, [file_content_text, ...])
    """
    if token is None:
        token = GITHUB_TOKEN
    owner, repo = parse_repo_url(repo_url)
    # PR details
    pr_text, pr_json = await fetch_pr_details(owner, repo, pr_number, token)
    files = await fetch_pr_files(owner, repo, pr_number, token)

    ref = pr_json.get('head', {}).get('sha')
    file_texts = []
    for f in files:
        status = f.get('status')
        filename = f.get('filename')
        if status in ['added', 'modified', 'renamed']:
            fetched_file_content = await fetch_file_content(owner, repo, filename, ref, token)
            formatted_file_content = format_file_content( fetched_file_content,filename)
            file_texts.append(formatted_file_content)
    return pr_text , file_texts

# async def main():
#     # Example usage:
#     url = "https://github.com/potpie-ai/potpie"
#     pr_number = 398

#     pr_details, files_contents = await run_pr_fetch(url, pr_number)

#     print(pr_details)
#     print("=" * 50)
#     print(len(files_contents))

#     for text in files_contents:
#         print(text)

# if __name__ == '__main__':
#     asyncio.run(main())

