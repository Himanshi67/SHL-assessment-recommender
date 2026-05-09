from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_chat_compare_two_assessments():
    payload = {
        "messages": [
            {"role": "user", "content": "What is the difference between OPQ and GSA?"}
        ]
    }

    response = client.post("/chat", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert "reply" in data
    assert "recommendations" in data
    assert "end_of_conversation" in data

    assert isinstance(data["recommendations"], list)
    assert data["recommendations"] == []
    assert data["end_of_conversation"] is False
    assert len(data["reply"]) > 0
