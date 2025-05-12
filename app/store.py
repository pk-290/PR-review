import os
import redis
import json


# Get Redis URL from environment variable with a default
REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')

# Create Redis connection
r = redis.Redis.from_url(REDIS_URL)

def init_task(task_id: str, repo_url, pr_number):
    r.hset(f"task:{task_id}:meta", mapping={
        "status": "pending",
        "repo_url": repo_url,
        "pr_number": pr_number
    })
    r.delete(f"task:{task_id}:hunks")
    r.delete(f"task:{task_id}:result")

def set_task_status(task_id: str, status: str):
    r.hset(f"task:{task_id}:meta", "status", status)


def get_task_status(task_id: str):
    print(task_id)
    meta = r.hgetall(f"task:{task_id}:meta")
    return {k.decode(): v.decode() for k,v in meta.items()} if meta else None


def set_final_result(task_id: str, result: dict):
    r.set(f"task:{task_id}:result", json.dumps(result))
    set_task_status(task_id, "completed")

def get_final_result(task_id: str):
    data = r.get(f"task:{task_id}:result")
    return json.loads(data) if data else None
