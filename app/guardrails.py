from typing import Tuple


def validate_query(query: str) -> Tuple[bool, str]:
    if not query or not query.strip():
        return False, 'empty query'
    if len(query) < 2:
        return False, 'query too short'
    if len(query) > 500:
        return False, 'query too long'
    return True, ''


def is_out_of_scope(text: str) -> bool:
    blocked_topics = ["legal advice", "salary negotiation", "labor law"]
    lowered = text.lower()
    return any(topic in lowered for topic in blocked_topics)
