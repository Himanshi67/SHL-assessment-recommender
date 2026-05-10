def test_chat_compare_two_assessments_returns_comparison_text(client, monkeypatch, mock_catalog):
    monkeypatch.setattr("app.routers.chat.load_clean_catalog", lambda: mock_catalog)
    payload = {"messages": [{"role": "user", "content": "What is the difference between OPQ and GSA?"}]}

    response = client.post("/chat", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data["reply"], str)
    assert data["recommendations"] == []
    assert data["end_of_conversation"] is False
    assert "opq" in data["reply"].lower()
    assert "gsa" in data["reply"].lower()


def test_chat_compare_uses_history_when_latest_message_is_ambiguous(client, monkeypatch, mock_catalog):
    monkeypatch.setattr("app.routers.chat.load_clean_catalog", lambda: mock_catalog)
    payload = {
        "messages": [
            {
                "role": "user",
                "content": "I am deciding between OPQ and GSA for a hiring process.",
            },
            {"role": "assistant", "content": "Sure, I can compare those two if useful."},
            {"role": "user", "content": "Please compare them."},
        ]
    }

    response = client.post("/chat", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["recommendations"] == []
    assert data["end_of_conversation"] is False
    assert "opq" in data["reply"].lower()
    assert "gsa" in data["reply"].lower()
