from collections import Counter
import pandas as pd, pytest
from pipeline.cleaning.dates import detect_family_conventions, parse_date

@pytest.fixture(scope="session")
def all_dates():
    return pd.read_csv("data/input/tech_news.csv", dtype=str).published_date.tolist()

@pytest.fixture(scope="session")
def conventions(all_dates):
    return detect_family_conventions(all_dates)

def test_slash_family_is_month_first(conventions):
    assert conventions["slash_numeric"] == "month_first"

def test_dash_family_is_split(conventions):
    assert conventions["dash_numeric_2digit"] == "split"

def test_corpus_status_counts(all_dates, conventions):
    c = Counter(parse_date(v, conventions).status for v in all_dates)
    assert c == {"parsed": 684, "ambiguous_resolved": 66}