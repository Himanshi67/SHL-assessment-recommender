import re
from pathlib import Path

import pytest

from app.recommender import validate_recommendations


TRACE_ROOT = Path(__file__).resolve().parents[2] / "GenAI_SampleConversations"


def _extract_user_turns(markdown_text: str):
    turns = re.split(r"### Turn\s+\d+", markdown_text)
    user_turns = []
    for block in turns[1:]:
        user_section = re.search(r"\*\*User\*\*(.*?)\*\*Agent\*\*", block, flags=re.S)
        if not user_section:
            continue
        quoted_lines = [
            line.strip()[1:].strip()
            for line in user_section.group(1).splitlines()
            if line.strip().startswith(">")
        ]
        user_text = " ".join(quoted_lines).strip()
        if user_text:
            user_turns.append(user_text)
    return user_turns


TRACE_FILES = sorted(TRACE_ROOT.glob("C*.md")) if TRACE_ROOT.exists() else []
pytestmark = pytest.mark.skipif(not TRACE_FILES, reason="Public conversation traces not found")


@pytest.mark.parametrize("trace_file", TRACE_FILES, ids=lambda p: p.stem)
def test_trace_replay_uses_full_history_and_respects_turn_cap(client, trace_file):
    text = trace_file.read_text(encoding="utf-8")
    user_turns = _extract_user_turns(text)
    assert len(user_turns) >= 1

    messages = []
    calls_made = 0

    for user_text in user_turns:
        if len(messages) >= 8:
            break

        messages.append({"role": "user", "content": user_text})
        response = client.post("/chat", json={"messages": messages})
        assert response.status_code == 200

        calls_made += 1
        data = response.json()
        assert set(data.keys()) == {"reply", "recommendations", "end_of_conversation"}
        assert isinstance(data["reply"], str)
        assert isinstance(data["end_of_conversation"], bool)
        assert validate_recommendations(data["recommendations"]) is True

        if len(messages) < 8:
            messages.append({"role": "assistant", "content": data["reply"]})

        if data["end_of_conversation"]:
            break

    assert calls_made >= 1
    assert len(messages) <= 8
