import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.tasks import analyze_pr
from unittest.mock import patch
import uuid

client = TestClient(app)

@pytest.fixture
def fake_pr_data():
    return {
        "repo_url": "https://github.com/example/repo",
        "pr_number": 42,
        "github_token": "ghp_dummyToken"
    }

def test_post_analyze_pr(fake_pr_data):
    # Patch Celery task to return fake UUID immediately
    fake_task_id = str(uuid.uuid4())
    with patch("app.routes.analyze_pr.delay") as mock_task:
        mock_task.return_value.id = fake_task_id
        response = client.post("/analyze-pr", json=fake_pr_data)
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == fake_task_id
        assert data["status"] == "queued"

def test_get_status_invalid():
    response = client.get("/status/fake-task-id")
    assert response.status_code == 200
    assert "status" in response.json()

def test_get_results_not_ready():
    response = client.get("/results/fake-task-id")
    assert response.status_code in [404, 200]  # if using Redis cache might return 200 with error
    # Based on your app logic, you can also assert error message

