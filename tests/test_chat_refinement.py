def test_chat_refinement_add_personality(client, monkeypatch, mock_catalog):
    monkeypatch.setattr("app.routers.chat.load_clean_catalog", lambda: mock_catalog)

    payload = {
        "messages": [
            {"role": "user", "content": "I am hiring a Java developer"},
            {
                "role": "assistant",
                "content": "Got it — what seniority level is the role, and do you want technical, aptitude, or personality assessments?",
            },
            {"role": "user", "content": "Mid-level, technical and aptitude"},
            {
                "role": "assistant",
                "content": "I found 5 SHL assessments that may fit your requirement.",
            },
            {"role": "user", "content": "Actually, also add personality tests"},
        ]
    }

    response = client.post("/chat", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert "reply" in data
    assert "recommendations" in data
    assert "end_of_conversation" in data

    assert data["end_of_conversation"] is False
    assert isinstance(data["recommendations"], list)
    assert len(data["recommendations"]) >= 1
    assert "updated" in data["reply"].lower() or "revised" in data["reply"].lower()
