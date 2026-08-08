from pathlib import Path
import pytest
from pipeline.layers.bronze import load_bronze_articles,load_bronze_companies

@pytest.fixture
def batch_id():
    return "batch_001"

@pytest.fixture
def article_path():
    return Path("data/input/tech_news.csv")

@pytest.fixture
def companies_path():
    return Path("data/input/company_metadata.json")

def test_bronze_articles_row_count(article_path, batch_id):
    df = load_bronze_articles(
        article_path,
        batch_id,
    )
    assert len(df) == 750
    assert "source_file" in df.columns
    assert "ingested_at" in df.columns
    assert "batch_id" in df.columns

def test_bronze_companies_row_count(companies_path, batch_id):
    df = load_bronze_companies(
        companies_path,
        batch_id,
    )

    assert len(df) == 21

def test_company_name_is_flattened(companies_path, batch_id):
    df = load_bronze_companies(
        companies_path,
        batch_id,
    )

    assert "OpenAI" in df["company_name"].values
    assert "NVIDIA" in df["company_name"].values
    assert "MongoDB" in df["company_name"].values