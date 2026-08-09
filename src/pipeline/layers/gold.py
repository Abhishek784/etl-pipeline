from __future__ import annotations
import pandas as pd

from pipeline.keys import article_key, company_key, quarantine_key, arr_observation_key

def _size_category(employee_count:int, small_max:int=9999, medium_max:int=30000)->str|None:
    if pd.isna(employee_count):
        return None
    n = int(employee_count)
    if n <= small_max:
        return "Small"
    if n <= medium_max:
        return "Medium"
    return "Large"


def build_dim_companies(silver_companies_df:pd.DataFrame,
                        settings: dict | None=None)->pd.DataFrame:
    settings = (settings or {}).get("company_size_bands", {})
    small_max = int(settings.get("small_max",9999))
    medium_max = int(settings.get("medium_max",30000))

    company_df= silver_companies_df.copy()

    output = pd.DataFrame({
        "company_key": company_df["company_name"].map(company_key),
        "company_name": company_df["company_name"],
        "industry_raw": company_df["industry"],
        "industry_std": company_df["industry_std"],
        "founded_year": company_df["founded_year"],
        "headquarters": company_df["headquarters"],
        "employee_count": company_df["employee_count"],
        "company_size_category": company_df["employee_count"].map(
            lambda n: _size_category(n, small_max, medium_max)
        ),
        "is_public": company_df["is_public"],
        "stock_ticker": company_df["stock_ticker"],       
    })
    return output.sort_values("company_key").reset_index(drop=True)


def build_dim_articles(silver_articles_df:pd.DataFrame ) -> pd.DataFrame:
    silver_df=silver_articles_df
    published=pd.to_datetime(silver_df["published_date"],errors="coerce")

    output=pd.DataFrame({
        "article_sk":silver_df["article_id"].map(article_key),
        "article_id": silver_df["article_id"],
        # null company_key is deliberate: an unmatched article is still an article
        "company_key": silver_df["company_name"].map(lambda n: company_key(n) if pd.notna(n) else None),
        "title": silver_df["title"],
        "summary": silver_df["summary"],
        "url": silver_df["url"],
        "author": silver_df["author"],
        "word_count": silver_df["word_count"],
        "published_date": silver_df["published_date"],
        "published_year": published.dt.year.astype("Int64"),
        "published_quarter": published.dt.quarter.astype("Int64"),
        "published_month": published.dt.month.astype("Int64"),
        "category_raw": silver_df["category_raw"],
        "category_std": silver_df["category_std"],
        "date_status": silver_df["date_status"],
        "company_match_method": silver_df["match_method"],
        "company_match_score": silver_df["match_score"],
    })
    return output.sort_values("article_id").reset_index(drop=True)



def build_fact_arr_observation(
    silver_articles: pd.DataFrame,
    dim_company: pd.DataFrame,
    batch_id: str,
) -> pd.DataFrame:
    s = silver_articles
    # ambiguous_resolved is a VALID observation carrying a flag -- only
    # 'invalid' is excluded. Using == "parsed" here would silently drop 66 rows.
    mask = (
        (s["arr_status"] == "ok")
        & (s["date_status"] != "invalid")
        & s["company_name"].notna()
    )
    f = s[mask].copy()
 
    founded = dim_company.set_index("company_name")["founded_year"]
    observed = pd.to_datetime(f["published_date"], errors="coerce")
 
    out = pd.DataFrame({
        "arr_observation_id": f["article_id"].map(arr_observation_key),
        "article_id": f["article_id"],
        "company_key": f["company_name"].map(company_key),
        "observed_date": f["published_date"],
        "arr_usd": f["arr_usd"].astype("Int64"),
        "source_currency": f["source_currency"],
        "source_value_raw": f["revenue_raw"],
        "parse_method": f["parse_method"],
        "fx_rate_applied": f["fx_rate_applied"],
        # computed per observation, not per company: it depends on the article date
        "company_age_at_obs": (
            observed.dt.year - f["company_name"].map(founded)
        ).astype("Int64"),
        "date_status": f["date_status"],
        "source_value_hash": f["source_value_hash"],
        "batch_id": batch_id,
    })
    return out.sort_values("arr_observation_id").reset_index(drop=True)


def build_quarantine_record(silver_articles: pd.DataFrame, batch_id: str) -> pd.DataFrame:
    """One row per FAILED VALUE, not per failed article.
 
    An article can fail two stages (no ARR and no company match) and produce
    two rows -- which is why quarantine_key includes the stage.
    """
    s = silver_articles
    frames = []
 
    stages = [
        ("arr_parse", s["arr_status"] != "ok", "arr_status", "revenue_raw"),
        ("company_match", s["match_method"].isin({"no_match", "low_confidence_match"}),
         "match_method", "company_name_raw"),
        ("date_parse", s["date_status"] == "invalid", "date_status", "published_date_raw"),
    ]
 
    for stage, mask, reason_col, value_col in stages:
        sub = s[mask]
        if sub.empty:
            continue
        frames.append(pd.DataFrame({
            "quarantine_id": [
                quarantine_key(sf, int(rn), stage)
                for sf, rn in zip(sub["source_file"], sub["source_row_num"])
            ],
            "source_file": sub["source_file"],
            "source_row_num": sub["source_row_num"],
            "article_id": sub["article_id"],
            "failure_stage": stage,
            "failure_reason": sub[reason_col],
            "raw_value": sub[value_col],
            "best_candidate": sub["match_candidate"] if "match_candidate" in sub else None,
            "match_score": sub["match_score"],
            "batch_id": batch_id,
        }))
 
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    return out.sort_values(["failure_stage", "article_id"]).reset_index(drop=True)
 