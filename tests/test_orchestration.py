from fastapi.testclient import TestClient
from src.orchestration.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_ask_agent_baseline():
    payload = {"query": "What is the policy on school infrastructure?", "user_id": "tester"}
    response = client.post("/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Infrastructure Recommendation" in data["response"]
    assert data["confidence"] == 0.98
    assert "sources" in data


def test_feedback_endpoint():
    payload = {"query": "Test query", "response": "Test response", "rating": 4}
    response = client.post("/feedback", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "feedback received"
