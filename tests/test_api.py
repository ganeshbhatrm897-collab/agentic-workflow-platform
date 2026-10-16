from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def client():
    return TestClient(create_app(Settings(max_workflows=2)))


def test_health_and_agents_endpoints():
    test_client = client()
    health = test_client.get("/api/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok", "demo_mode": True, "execution": "sequential-local"}
    agents = test_client.get("/api/agents").json()
    assert len(agents) == 6
    assert {agent["id"] for agent in agents} >= {"intake", "planning", "execution", "validation"}


def test_examples_have_four_runnable_scenarios():
    examples = client().get("/api/workflows/examples").json()
    assert {example["scenario"] for example in examples} == {"meeting", "project", "document", "support"}
    assert all(example["task"] for example in examples)


def test_all_builtin_scenarios_execute_successfully():
    test_client = client()
    for example in test_client.get("/api/workflows/examples").json():
        response = test_client.post(
            "/api/workflows",
            json={"task": example["task"], "scenario": example["scenario"]},
        )
        assert response.status_code == 201
        assert response.json()["status"] == "completed"


def test_create_history_detail_schema_and_full_workflow():
    test_client = client()
    payload = {"task": "Text: Name: Jordan\nEmail: j@example.test", "scenario": "document"}
    response = test_client.post("/api/workflows", json=payload)
    assert response.status_code == 201
    record = response.json()
    assert record["workflow_id"]
    assert record["status"] == "completed"
    assert len(record["plan"]) == 4
    assert record["plan"][2]["validation"]["valid"] is True
    assert record["result"]["execute"]["fields"]["email"] == ["j@example.test"]
    assert test_client.get(f"/api/workflows/{record['workflow_id']}").json() == record
    history = test_client.get("/api/workflows").json()
    assert history[0]["workflow_id"] == record["workflow_id"]
    assert "result" not in history[0]


def test_invalid_and_whitespace_requests_have_helpful_errors():
    test_client = client()
    assert test_client.post("/api/workflows", json={"task": ""}).status_code == 422
    whitespace = test_client.post("/api/workflows", json={"task": "   "})
    assert whitespace.status_code == 422
    assert "at least 1 character" in whitespace.text


def test_unknown_workflow_returns_404_and_history_is_bounded():
    test_client = client()
    assert test_client.get("/api/workflows/missing").status_code == 404
    for index in range(3):
        assert test_client.post("/api/workflows", json={"task": f"Task {index}"}).status_code == 201
    history = test_client.get("/api/workflows").json()
    assert len(history) == 2
    assert history[0]["task"] == "Task 2"


def test_demo_mode_without_credentials_and_frontend_are_available():
    test_client = client()
    assert test_client.get("/api/health").json()["demo_mode"] is True
    page = test_client.get("/")
    assert page.status_code == 200
    assert "Agentic Workflow" in page.text
    assert test_client.get("/static/app.js").status_code == 200
