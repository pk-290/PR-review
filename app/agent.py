from app.store import get_all_hunk_results, set_final_result
from app.llm_garden import execute_chain
from typing import List ,Optional
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

class final_review(BaseModel):
    file:List[str]
    issues:List[str]
    summary:dict

final_review_parser = JsonOutputParser(pydantic_object = final_review)

class ReviewAgent:
    def __init__(self, task_id, repo_url, pr_number, token):
        self.task_id = task_id
        self.repo = repo_url
        self.pr = pr_number
        self.token = token

    def synthesize_and_post(self):
        # 1) gather
        hunk_results = get_all_hunk_results(self.task_id)

        # 2) prompt
        prompt_template = """You are a senior code reviewer. Here are per-hunk findings:\n
            {hunk_results}\n
            Produce a PR-level JSON report with files[], issues[], summary:dict."""
        input_vars = {"hunk_results":hunk_results}
        resp = execute_chain(prompt_template,input_vars,final_review_parser)
        # report = resp.choices[0].message.content  # assume JSON
        # 3) persist & post
        set_final_result(self.task_id, resp)
