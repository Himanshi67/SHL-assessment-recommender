from app.recommender import (
    build_recommendations,
    detect_requested_seniority,
    search_catalog,
    should_ask_clarification,
    validate_recommendations,
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
            "url": "https://www.shl.com/products/product-catalog/view/data-entry-test/",
            "description": "Data entry skills assessment",
            "tags": "Knowledge & Skills",
            "test_type": "Knowledge & Skills",
            "job_levels": "Entry-Level",
            "languages": "English (USA)",
        }
    ]
    results = search_catalog("data entry", catalog, top_k=3)
    assert len(results) >= 1
    assert results[0]["entity_id"] == "1"


def test_search_catalog_respects_top_k():
    catalog = [
        {
            "entity_id": "1",
            "name": "Data Entry Test",
            "url": "https://www.shl.com/products/product-catalog/view/data-entry-test/",
            "description": "Data entry assessment",
            "tags": "Knowledge & Skills",
            "test_type": "Knowledge & Skills",
            "job_levels": "Entry-Level",
            "languages": "English (USA)",
        },
        {
            "entity_id": "2",
            "name": "Data Entry Simulation",
            "url": "https://www.shl.com/products/product-catalog/view/data-entry-simulation/",
            "description": "Simulation for data entry",
            "tags": "Simulations",
            "test_type": "Simulations",
            "job_levels": "Entry-Level",
            "languages": "English (USA)",
        },
        {
            "entity_id": "3",
            "name": "Data Entry Operator Test",
            "url": "https://www.shl.com/products/product-catalog/view/data-entry-operator-test/",
            "description": "Operator assessment for data entry work",
            "tags": "Knowledge & Skills",
            "test_type": "Knowledge & Skills",
            "job_levels": "Entry-Level",
            "languages": "English (USA)",
        },
    ]
    results = search_catalog("data entry", catalog, top_k=2)
    assert len(results) == 2


def test_search_catalog_filters_by_mid_level():
    catalog = [
        {
            "entity_id": "1",
            "name": "Core Java Entry Level (New)",
            "url": "https://www.shl.com/products/product-catalog/view/core-java-entry-level-new/",
            "description": "Java basics assessment",
            "tags": "Knowledge & Skills",
            "test_type": "Knowledge & Skills",
            "job_levels": "Entry-Level",
            "languages": "English (USA)",
        },
        {
            "entity_id": "2",
            "name": "Java Design Patterns (New)",
            "url": "https://www.shl.com/products/product-catalog/view/java-design-patterns-new/",
            "description": "Java design patterns for professional developers",
            "tags": "Knowledge & Skills",
            "test_type": "Knowledge & Skills",
            "job_levels": "Mid-Professional",
            "languages": "English (USA)",
        },
    ]
    results = search_catalog("Java developer mid-level technical", catalog, top_k=5)
    assert len(results) >= 1
    assert all("Mid-Professional" in item["job_levels"] for item in results)


def test_build_recommendations_skips_invalid_urls_and_duplicates():
    items = [
        {
            "name": "A",
            "url": "https://www.shl.com/products/product-catalog/view/a/",
            "test_type": "K",
        },
        {
            "name": "A duplicate",
            "url": "https://www.shl.com/products/product-catalog/view/a/",
            "test_type": "K",
        },
        {
            "name": "Bad URL",
            "url": "https://example.com/not-allowed",
            "test_type": "K",
        },
        {
            "name": "B",
            "url": "https://www.shl.com/products/product-catalog/view/b/",
            "test_type": "A",
        },
    ]
    recommendations = build_recommendations(items)
    assert len(recommendations) == 2
    assert validate_recommendations(recommendations) is True


def test_validate_recommendations_rejects_invalid_payload():
    invalid = [
        {
            "name": "Invalid",
            "url": "https://example.com/invalid",
            "test_type": "K",
        }
    ]
    assert validate_recommendations(invalid) is False
