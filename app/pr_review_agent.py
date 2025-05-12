from app.llm_garden import aexecute_chain
from typing import List ,Optional,Literal
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from app.static_analyzer_tools import run_static_analyzer 
from app.logging_wrapper import log_async_exceptions,log_exceptions


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

@log_async_exceptions
async def review_hunk(pr_info:str,pr_file:str):
    prompt_template = """You are a PR review assistant. Analyze the following code hunk and the static analysis report. Then provide issues categorized as:

1. style: Code style and formatting issues
2. bug: Potential bugs or errors
3. performance: Suggestions to improve performance
4. best_practice: Adherence to best practices
=== PR Info ====
{pr_info}

=== Code Hunk ===
{code_hunk}

=== Static Analysis Report ===
{static_report}
""" 
  
    static_report = run_static_analyzer(pr_file)
    input_vars = {"pr_info":pr_info,"code_hunk":pr_file,"static_report":static_report}
    review = await aexecute_chain(prompt_template,input_vars,final_review_parser)
    return review


