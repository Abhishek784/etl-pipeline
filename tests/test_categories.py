import pytest
from pipeline.cleaning.categories import standardise_category

@pytest.fixture
def category_map():
    return {
        "AI_ML": [
            "AI/ML",
            "Artificial Intelligence",
            "Machine Learning",
            "AI & ML",
        ],
        "CLOUD": [
            "Cloud Computing",
            "Cloud",
            "Cloud Services",
            "SaaS",
        ],
        "FINTECH": [
            "Financial Technology",
            "FinTech",
            "Finance",
        ],
        "DATA": [
            "Big Data",
            "Analytics",
            "Data Analytics",
        ],
        "CYBERSEC": [
            "Cybersecurity",
            "Security",
            "InfoSec",
        ],
        "SOFTWARE": [
            "Software",
            "Enterprise Software",
        ],
    }

@pytest.mark.parametrize(
    "raw, expected",
    [
        ("AI/ML", "AI_ML"),
        ("Artificial Intelligence", "AI_ML"),
        ("Machine Learning", "AI_ML"),

        ("Cloud", "CLOUD"),
        ("Cloud Services", "CLOUD"),

        ("FinTech", "FINTECH"),
        ("Finance", "FINTECH"),

        ("Analytics", "DATA"),
        ("Data Analytics", "DATA"),

        ("Cybersecurity", "CYBERSEC"),
        ("InfoSec", "CYBERSEC"),

        ("Software", "SOFTWARE"),
        ("Enterprise Software", "SOFTWARE"),
    ],
)
def test_standardise_category(raw, expected, category_map):
    result = standardise_category(raw, category_map)
    assert result == expected