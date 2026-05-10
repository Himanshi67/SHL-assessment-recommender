from app.recommender import validate_recommendations


def test_chat_requires_messages_field(client):
    response = client.post("/chat", json={})
    assert response.status_code == 422


def test_chat_clarification_for_vague_query_returns_schema(client, monkeypatch, mock_catalog):
    monkeypatch.setattr("app.routers.chat.load_clean_catalog", lambda: mock_catalog)
    payload = {"messages": [{"role": "user", "content": "I am hiring a Java developer"}]}

    response = client.post("/chat", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert set(data.keys()) == {"reply", "recommendations", "end_of_conversation"}
    assert isinstance(data["reply"], str)
    assert data["recommendations"] == []
    assert data["end_of_conversation"] is False


def test_chat_recommendation_for_grounded_query_returns_schema(client, monkeypatch, mock_catalog):
    monkeypatch.setattr("app.routers.chat.load_clean_catalog", lambda: mock_catalog)
    payload = {
        "messages": [
            {"role": "user", "content": "I am hiring a Java developer"},
            {
                "role": "assistant",
                "content": "What seniority level is the role, and do you want technical, aptitude, or personality assessments?",
            },
            {"role": "user", "content": "Mid-level, technical and aptitude"},
        ]
    }

    response = client.post("/chat", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert set(data.keys()) == {"reply", "recommendations", "end_of_conversation"}
    assert isinstance(data["reply"], str)
    assert isinstance(data["recommendations"], list)
    assert 1 <= len(data["recommendations"]) <= 10
    assert data["end_of_conversation"] is False
    assert validate_recommendations(data["recommendations"]) is True


def test_chat_response_recommendations_are_unique_and_shl_urls(client, monkeypatch, mock_catalog):
    dupe_catalog = mock_catalog + [dict(mock_catalog[0])]
    monkeypatch.setattr("app.routers.chat.load_clean_catalog", lambda: dupe_catalog)

    payload = {
        "messages": [
            {"role": "user", "content": "I am hiring a Java developer"},
            {"role": "assistant", "content": "Please share seniority and preference."},
            {"role": "user", "content": "Mid-level, technical and personality"},
        ]
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200

    data = response.json()
    recommendations = data["recommendations"]
    assert validate_recommendations(recommendations) is True

    urls = [rec["url"].lower() for rec in recommendations]
    assert len(urls) == len(set(urls))
    assert all(url.startswith("https://www.shl.com/") for url in urls)


def test_chat_does_not_end_conversation_on_mixed_confirmation_and_refinement(client, monkeypatch, mock_catalog):
    monkeypatch.setattr("app.routers.chat.load_clean_catalog", lambda: mock_catalog)
    payload = {
        "messages": [
            {"role": "user", "content": "I am hiring a Java developer"},
            {
                "role": "assistant",
                "content": "What seniority level is the role, and do you want technical, aptitude, or personality assessments?",
            },
            {"role": "user", "content": "Mid-level, technical and aptitude"},
            {"role": "assistant", "content": "Here is a shortlist to start from."},
            {"role": "user", "content": "Thanks, also add personality tests."},
        ]
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data["recommendations"], list)
    assert len(data["recommendations"]) >= 1
    assert data["end_of_conversation"] is False
