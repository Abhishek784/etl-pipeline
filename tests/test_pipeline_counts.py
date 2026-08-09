from collections import Counter


def test_silver_row_count(silver_articles):
    assert len(silver_articles) == 750
    assert silver_articles.article_id.is_unique



def test_arr_status_distribution(silver_articles):
    assert Counter(silver_articles.arr_status) == {
        "ok": 558, "missing": 107, "not_disclosed": 85,
    }


def test_arr_parse_methods(silver_articles):
    ok = silver_articles[silver_articles.arr_status == "ok"]    
    assert Counter(ok.parse_method) == {"single": 500, "range_midpoint": 58}


def test_date_status_distribution(silver_articles):
    assert Counter(silver_articles.date_status) == {
        "parsed": 684, "ambiguous_resolved": 66,
    }


def test_category_distribution(silver_articles):
    assert Counter(silver_articles.category_std) == {
        "AI_ML": 161, "CLOUD": 153, "DATA": 131,
        "FINTECH": 124, "CYBERSEC": 104, "SOFTWARE": 77,
    }


def test_company_match_distribution(silver_articles):
    c = Counter(silver_articles.match_method)
    assert c["exact"] == 665
    assert c["normalized"] == 36
    assert c["alias"] + c["alias_lossy"] == 24
    assert c.get("fuzzy", 0) == 0, "fuzzy should not fire: tiers 1-2 cover this corpus"
    assert c["no_match"] == 25
    assert sum(c.values()) == 750


def test_gold_row_counts(gold_tables):
    assert len(gold_tables["dim_company"]) == 21
    assert len(gold_tables["dim_article"]) == 750
    assert len(gold_tables["fact_arr_observation"]) == 538
    # 217 FAILURES, not 212 excluded articles: 5 rows fail two stages each
    assert len(gold_tables["quarantine_record"]) == 217


def test_fact_includes_ambiguous_dates(gold_tables):
    """44 ambiguous_resolved rows belong in the fact table. A flag marks
    confidence, not invalidity -- filtering on == 'parsed' would drop them."""
    c = Counter(gold_tables["fact_arr_observation"].date_status)
    assert c == {"parsed": 494, "ambiguous_resolved": 44}


def test_referential_integrity(gold_tables):
    fact, dim_c, dim_a = (gold_tables[k] for k in
                          ("fact_arr_observation", "dim_company", "dim_article"))
    keys = set(dim_c.company_key)
    assert fact.company_key.isin(keys).all()
    assert dim_a.company_key.dropna().isin(keys).all()
    assert dim_a.company_key.isna().sum() == 25
    assert fact.article_id.isin(set(dim_a.article_id)).all()


def test_fact_primary_key_and_domain(gold_tables):
    fact = gold_tables["fact_arr_observation"]
    assert fact.arr_observation_id.is_unique
    assert (fact.arr_usd > 0).all()
    assert fact.observed_date.notna().all()