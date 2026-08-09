import pytest
from pipeline.cleaning.categories import standardise_category, build_category_lookup

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

@pytest.fixture
def lookup(category_map):
    return build_category_lookup(category_map)

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


def test_standardise_category(raw, expected, lookup):
    assert standardise_category(raw, lookup) == expected


@pytest.mark.parametrize("raw", ["Quantum Computing", "Blockchain", "", None])
def test_unmapped_returns_unknown(raw, lookup):
    assert standardise_category(raw, lookup) == "UNKNOWN"


@pytest.mark.parametrize("raw", ["ai/ml", "  AI/ML  ", "Ai/Ml"])
def test_matching_is_case_and_whitespace_insensitive(raw, lookup):
    assert standardise_category(raw, lookup) == "AI_ML"