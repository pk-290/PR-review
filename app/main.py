import uvicorn
import os
from fastapi import FastAPI, HTTPException
from app.models import AnalyzePRRequest, StatusResponse, ResultsResponse
from app.tasks import analyze_pr
from app.store import get_task_status, get_final_result
from logging_wrapper import log_async_exceptions,log_exceptions

app = FastAPI()

@log_exceptions
@app.post("/analyze-pr")
def start(req: AnalyzePRRequest):
    # print(req)
    task = analyze_pr.delay(req.repo_url, req.pr_number, req.github_token)
    return {"task_id": task.id}

@log_exceptions
@app.get("/status/{task_id}", response_model=StatusResponse)
def status(task_id: str):
    meta = get_task_status(task_id)
    if not meta: raise HTTPException(404, "Not found")
    return {"task_id": task_id, "status": meta["status"]}

@log_exceptions
@app.get("/results/{task_id}")
def results(task_id: str):
    status = get_task_status(task_id)
    if not status or status["status"] != "completed":
        raise HTTPException(404, "Results not ready")
    final_review = get_final_result(task_id)
    res = {"task_id":task_id , "status": "completed" , "results" : final_review}
    # print(res)
    return res


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)