import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_catalog():
    return [
        {
            "entity_id": "1",
            "name": "Java Design Patterns (New)",
            "url": "https://www.shl.com/products/product-catalog/view/java-design-patterns-new/",
            "description": "Java design patterns for professional developers",
            "tags": "Knowledge & Skills",
            "test_type": "Knowledge & Skills",
            "job_levels": "Mid-Professional",
            "languages": "English (USA)",
            "duration": "12 minutes",
        },
        {
            "entity_id": "2",
            "name": "Java Personality Profile",
            "url": "https://www.shl.com/products/product-catalog/view/java-personality-profile/",
            "description": "Personality and behaviour assessment for developers",
            "tags": "Personality & Behavior",
            "test_type": "Personality & Behavior",
            "job_levels": "Mid-Professional",
            "languages": "English (USA)",
            "duration": "10 minutes",
        },
        {
            "entity_id": "3",
            "name": "Java Aptitude Test",
            "url": "https://www.shl.com/products/product-catalog/view/java-aptitude-test/",
            "description": "Aptitude and ability test for Java roles",
            "tags": "Ability & Aptitude",
            "test_type": "Ability & Aptitude",
            "job_levels": "Mid-Professional",
            "languages": "English (USA)",
            "duration": "15 minutes",
        },
        {
            "entity_id": "4",
            "name": "OPQ",
            "url": "https://www.shl.com/products/product-catalog/view/occupational-personality-questionnaire-opq32r/",
            "description": "Occupational personality questionnaire",
            "tags": "Personality & Behavior",
            "test_type": "Personality & Behavior",
            "job_levels": "Manager, Mid-Professional",
            "languages": "English (USA)",
            "duration": "20 minutes",
        },
        {
            "entity_id": "5",
            "name": "GSA",
            "url": "https://www.shl.com/products/product-catalog/view/global-skills-assessment/",
            "description": "Global skills assessment",
            "tags": "Ability & Aptitude",
            "test_type": "Ability & Aptitude",
            "job_levels": "Entry-Level, Mid-Professional, Manager",
            "languages": "English (USA)",
            "duration": "18 minutes",
        },
    ]
