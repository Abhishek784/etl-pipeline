from __future__ import annotations
from collections import Counter
import pytest
from pipeline.layers.bronze import load_bronze_articles
from pipeline.layers.bronze import load_bronze_companies
from pipeline.layers.silver import build_silver_companies
from pipeline.layers.silver import build_silver_articles
from pipeline.cleaning.companies import build_registry
from pathlib import Path     

@pytest.fixture
def category_lookup() -> dict[str, str]:
    return {
        "AI/ML": "AI_ML",
        "Data Analytics": "DATA",
        "SaaS": "CLOUD",
        "Cyber Security": "SECURITY",
        "FinTech": "FINTECH",
        "HealthTech": "HEALTH",
    }


@pytest.fixture
def bronze_data():
    bronze_articles = load_bronze_articles(
        Path("data/input/tech_news.csv"),
        batch_id="test_batch",
    )
    bronze_companies = load_bronze_companies(
        Path("data/input/company_metadata.json"),
        batch_id="test_batch",
    )
    return bronze_articles, bronze_companies


def test_silver_companies_row_count(
    bronze_data,
    category_lookup,
):
    _, bronze_companies = bronze_data

    silver = build_silver_companies(
        bronze_companies,
        category_lookup,
    )

    assert len(silver) == 21

def test_company_column_types(
    bronze_data,
    category_lookup,
):
    _, bronze_companies = bronze_data

    silver = build_silver_companies(
        bronze_companies,
        category_lookup,
    )

    assert silver["founded_year"].dtype == "Int64"
    assert silver["employee_count"].dtype == "Int64"
    assert silver["is_public"].dtype == "boolean"



@pytest.fixture
def registry():
    return build_registry(
        [
            "OpenAI",
            "NVIDIA",
            "MongoDB",
            "Stripe",
            "Databricks",
            "Snowflake",
            "Confluent",
            "Palantir",
            "Anthropic",
            "Cohere",
            "Scale AI",
            "DataRobot",
            "UiPath",
            "Fivetran",
            "dbt Labs",
            "Hugging Face",
            "Mistral AI",
            "Perplexity",
            "Canva",
            "Zapier",
            "Notion",
        ]
    )
def test_silver_articles_row_count(
    bronze_data,
    registry,
    category_lookup,
):
    bronze_articles, _ = bronze_data

    silver = build_silver_articles(
        bronze_articles,
        registry,
        category_lookup
    )

    assert len(silver) == 750

def test_article_ids_unique(
    bronze_data,
    registry,
    category_lookup,
):
    bronze_articles, _ = bronze_data

    silver = build_silver_articles(
        bronze_articles,
        registry,
        category_lookup,
    )

    assert silver.article_id.is_unique

# #Test 6 — Revenue Distribution
# def test_arr_status_distribution(
#     bronze_data,
#     registry,
#     category_lookup,
# ):
#     bronze_articles, _ = bronze_data

#     silver = build_silver_articles(
#         bronze_articles,
#         registry,
#         category_lookup,
#     )

#     counts = Counter(silver.arr_status)

#     assert counts == {
#         "ok": 558,
#         "missing": 107,
#         "not_disclosed": 85,
#     }


# def test_category_distribution(
#     bronze_data,
#     registry,
#     category_lookup,
# ):
#     bronze_articles, _ = bronze_data

#     silver = build_silver_articles(
#         bronze_articles,
#         registry,
#         category_lookup,
#     )

#     counts = Counter(silver.category_std)

#     assert counts == {
#         "AI_ML": 161,
#         "DATA": 153,
#         "CLOUD": 131,
#         "SECURITY": 124,
#         "FINTECH": 104,
#         "HEALTH": 77,
#     }