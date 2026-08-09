from __future__ import annotations

import pandas as pd

EXPORT_COLUMNS = [
    "article_id", "title", "company_name", "published_date", "category",
    "arr_usd", "summary", "url", "industry", "founded_year", "headquarters",
    "employee_count", "is_public", "stock_ticker", "company_age",
    "company_size_category",
]


def build_ai_articles_enriched(
    fact: pd.DataFrame,
    dim_article: pd.DataFrame,
    dim_company: pd.DataFrame,
    settings: dict,
    embeddings: pd.DataFrame | None = None,
    similarity: pd.DataFrame | None = None,
) -> pd.DataFrame:
    cfg = settings["ai_export"]
    ai_code = cfg.get("ai_category", "AI_ML")

    df = (
        fact.merge(
            dim_article.drop(columns=["company_key"]), on="article_id", how="inner"
        )
        .merge(dim_company, on="company_key", how="inner")
    )

    # The OR is load-bearing: 68 rows qualify on article category alone,
    # 41 on company industry alone, only 15 on both.
    is_ai = (df["category_std"] == ai_code) | (df["industry_std"] == ai_code)
    in_window = df["published_year"].between(cfg["year_min"], cfg["year_max"])
    above_floor = df["arr_usd"] > cfg["min_arr_usd"]

    df = df[is_ai & in_window & above_floor].copy()

    df["category"] = df["category_raw"]
    df["industry"] = df["industry_raw"]
    df["company_age"] = df["company_age_at_obs"]

    if embeddings is not None:
        df = df.merge(embeddings[["article_id", "embedding"]], on="article_id", how="left")
    if similarity is not None:
        top = (
            similarity.sort_values(["article_id", "rank"])
            .groupby("article_id")["similar_article_id"]
            .apply(lambda s: ",".join(s))
            .rename("top_similar_articles")
            .reset_index()
        )
        df = df.merge(top, on="article_id", how="left")

    cols = EXPORT_COLUMNS + [c for c in ("embedding", "top_similar_articles") if c in df]
    return df[cols].sort_values("article_id").reset_index(drop=True)