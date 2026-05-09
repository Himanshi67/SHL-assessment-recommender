def test_chat_clarification_for_vague_query(client, monkeypatch, mock_catalog):
    monkeypatch.setattr("app.routers.chat.load_clean_catalog", lambda: mock_catalog)

    payload = {
        "messages": [{"role": "user", "content": "I am hiring a Java developer"}]
    }

    response = client.post("/chat", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert "reply" in data
    assert "recommendations" in data
    assert "end_of_conversation" in data

    assert data["recommendations"] == []
    assert data["end_of_conversation"] is False
    assert "seniority" in data["reply"].lower() or "technical" in data["reply"].lower()


def test_chat_returns_recommendations_when_context_is_complete(
    client, monkeypatch, mock_catalog
):
    monkeypatch.setattr("app.routers.chat.load_clean_catalog", lambda: mock_catalog)

    payload = {
        "messages": [
            {"role": "user", "content": "I am hiring a Java developer"},
            {
                "role": "assistant",
                "content": "Got it — what seniority level is the role, and do you want technical, aptitude, or personality assessments?",
            },
            {"role": "user", "content": "Mid-level, technical and aptitude"},
        ]
    }

    response = client.post("/chat", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert "reply" in data
    assert "recommendations" in data
    assert "end_of_conversation" in data

    assert isinstance(data["recommendations"], list)
    assert len(data["recommendations"]) >= 1
    assert data["end_of_conversation"] is False

    first = data["recommendations"][0]
    assert "name" in first
    assert "url" in first
    assert "test_type" in first


def test_chat_compare_request_returns_no_recommendations(
    client, monkeypatch, mock_catalog
):
    monkeypatch.setattr("app.routers.chat.load_clean_catalog", lambda: mock_catalog)

    payload = {"messages": [{"role": "user", "content": "Compare OPQ and GSA"}]}

    response = client.post("/chat", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert "reply" in data
    assert "recommendations" in data
    assert "end_of_conversation" in data

    assert isinstance(data["recommendations"], list)
    assert data["recommendations"] == []
    assert data["end_of_conversation"] is False
