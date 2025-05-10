from pydantic import BaseModel
from typing import List, Optional, Literal

class AnalyzePRRequest(BaseModel):
    repo_url: str
    pr_number: int
    github_token: Optional[str]

class StatusResponse(BaseModel):
    task_id: str
    status: Literal["pending","processing","completed","failed"]

class Issue(BaseModel):
    type: Literal["style","bug","performance","best_practice"]
    line: int
    description: str
    suggestion: str

class FileResult(BaseModel):
    name: str
    issues: List[Issue]

class Summary(BaseModel):
    total_files: int
    total_issues: int
    critical_issues: int

class ResultsResponse(BaseModel):
    task_id: str
    status: Literal["completed"]
    results: dict  # {"files": List[FileResult], "summary": Summary}
