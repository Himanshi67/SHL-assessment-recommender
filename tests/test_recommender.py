from app.recommender import (
    search_catalog,
    should_ask_clarification,
    detect_requested_seniority,
)


def test_detect_requested_seniority_mid():
    assert detect_requested_seniority("Mid-level, technical and aptitude") == "mid"


def test_should_ask_clarification_for_vague_input():
    messages = [{"role": "user", "content": "I need an assessment"}]
    assert should_ask_clarification(messages) is True


def test_should_not_ask_clarification_when_context_is_enough():
    messages = [
        {"role": "user", "content": "I am hiring a Java developer"},
        {"role": "user", "content": "Mid-level, technical and aptitude"},
    ]
    assert should_ask_clarification(messages) is False


def test_search_catalog_basic_match():
    catalog = [
        {
            "entity_id": "1",
            "name": "Data Entry Test",
            "url": "https://example.com/test",
            "description": "Data entry skills assessment",
            "tags": "Knowledge & Skills",
            "test_type": "Knowledge & Skills",
            "job_levels": "Entry-Level",
            "languages": "English (USA)",
        }
    ]

    res = search_catalog("data entry", catalog, top_k=3)

    assert len(res) >= 1
    assert res[0]["entity_id"] == "1"


def test_search_catalog_respects_top_k():
    catalog = [
        {
            "entity_id": "1",
            "name": "Data Entry Test",
            "url": "https://example.com/1",
            "description": "Data entry assessment",
            "tags": "Knowledge & Skills",
            "test_type": "Knowledge & Skills",
            "job_levels": "Entry-Level",
            "languages": "English (USA)",
        },
        {
            "entity_id": "2",
            "name": "Data Entry Simulation",
            "url": "https://example.com/2",
            "description": "Simulation for data entry",
            "tags": "Simulations",
            "test_type": "Simulations",
            "job_levels": "Entry-Level",
            "languages": "English (USA)",
        },
        {
            "entity_id": "3",
            "name": "Data Entry Operator Test",
            "url": "https://example.com/3",
            "description": "Operator assessment for data entry work",
            "tags": "Knowledge & Skills",
            "test_type": "Knowledge & Skills",
            "job_levels": "Entry-Level",
            "languages": "English (USA)",
        },
    ]

    res = search_catalog("data entry", catalog, top_k=2)

    assert len(res) == 2


def test_search_catalog_filters_by_mid_level():
    catalog = [
        {
            "entity_id": "1",
            "name": "Core Java Entry Level (New)",
            "url": "https://example.com/1",
            "description": "Java basics assessment",
            "tags": "Knowledge & Skills",
            "test_type": "Knowledge & Skills",
            "job_levels": "Entry-Level",
            "languages": "English (USA)",
        },
        {
            "entity_id": "2",
            "name": "Java Design Patterns (New)",
            "url": "https://example.com/2",
            "description": "Java design patterns for professional developers",
            "tags": "Knowledge & Skills",
            "test_type": "Knowledge & Skills",
            "job_levels": "Mid-Professional",
            "languages": "English (USA)",
        },
    ]

    res = search_catalog("Java developer mid-level technical", catalog, top_k=5)

    assert len(res) >= 1
    assert all("Mid-Professional" in item["job_levels"] for item in res)
