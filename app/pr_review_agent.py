from app.llm_garden import aexecute_chain
from typing import List ,Optional,Literal
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

class issue_model(BaseModel):
    type: Literal["style", "bug", "performance", "best_practice"]
    line: int
    description: str
    suggestion: str

class final_review(BaseModel):
    file_name:str
    issues:List[issue_model]
    summary:dict

final_review_parser = JsonOutputParser(pydantic_object = final_review)

async def review_hunk(pr_info:str,pr_file:str):
    prompt_template = """You are a code review assistant. You will be given a unified diff hunk of changes for a single file. Your job is to analyze the changes and identify:

    1. Code style and formatting issues (“style”)
    2. Potential bugs or errors (“bug”)
    3. Performance improvements (“performance”)
    4. Best practices (“best_practice”)

    **Guidelines:**
    - Only report issues that are introduced or exposed by the diff.
    - Use the “new” file’s line numbers (after patch applied).
    - Be concise: one issue per JSON object.
    - If no issues are found, return `"issues": []`.
    PR details:{pr_info}
    Here is file diff hunk {pr_file}"""
    input_vars = {"pr_info":pr_info,"pr_file":pr_file}
    review = await aexecute_chain(prompt_template,input_vars,final_review_parser)
    return review


