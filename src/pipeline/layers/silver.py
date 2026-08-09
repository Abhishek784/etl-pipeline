from pipeline.cleaning.companies import resolve_company
import pandas as pd
from pipeline.cleaning.dates import detect_family_conventions,parse_date
from pipeline.cleaning.revenue import parse_revenue
from dataclasses import asdict
import hashlib

def _to_none(value):
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


#   silver for company_metadata.json
def build_silver_companies( df_bronze_companies:pd.Dataframe, category_lookup:dict ) -> pd.Dataframe:
    df_silver_companies = df_bronze_companies.copy()
    df_silver_companies = df_silver_companies.map(_to_none)

    df_silver_companies["founded_year"] = pd.to_numeric(
        df_silver_companies["founded_year"],
        errors="coerce",
    ).astype("Int64")

    df_silver_companies["employee_count"] = pd.to_numeric(
        df_silver_companies["employee_count"],
        errors="coerce",
    ).astype("Int64")

    df_silver_companies["is_public"] = (
        df_silver_companies["is_public"]
        .map(
            lambda x: None
            if x is None
            else str(x).strip().lower() == "true"
        )
        .astype("boolean")
    )

    df_silver_companies["industry_std"] = ( df_silver_companies["industry"].map(category_lookup))
    return df_silver_companies

#   silver for tech_news.csv
def build_silver_articles(bronze_articles: pd.DataFrame, registry,
                        category_lookup: dict) -> pd.DataFrame:
    silver = bronze_articles.copy()
    silver = silver.map(_to_none)
    conventions = detect_family_conventions(
        silver["published_date"].tolist()
    )

    #step1
    category_results = pd.DataFrame(
    {
        "category_raw": silver["category"],
        "category_std": silver["category"].map(
            lambda x: category_lookup.get(x)
        ),
    },
    index=silver.index,
    )
    
    #step2
    date_results = date_parsing(silver, conventions)
    
    #step3
    company_results = company_name_parsing(silver, registry)
    
    #step4
    revenue_results = revenue_parsing(silver)

    #step5
    audit_results = pd.DataFrame(
        {
            "source_value_hash": silver.apply(
                build_source_hash,
                axis=1,
            )
        },
        index=silver.index,
    )
    silver_articles = pd.concat(
        [
            # Lineage
            silver[
                ["source_file","source_row_num","batch_id"]
            ],
            # Identity
            silver[
                ["article_id",]
            ],
            # Passthrough
            silver[
                ["title","summary","url","author","word_count",]
            ],
            category_results,
            date_results,
            company_results,
            revenue_results,
            audit_results,
        ],
        axis=1,
    )
    #silver_articles=build_column_order(silver_articles)
    return silver_articles


def date_parsing(silver:pd.DataFrame,conventions:dict):
    parsed_dates = silver["published_date"].map(
        lambda value: parse_date(value, conventions)
    )
    date_results = pd.DataFrame(
        [asdict(result) for result in parsed_dates],
        index=silver.index,
    )
    date_results = date_results.rename(
        columns={
            "parsed_date": "published_date",
            "status": "date_status",
            "family": "date_family",
            "convention_used": "date_convention_used",
        }
    )
    date_results.insert(
        0,
        "published_date_raw",
        silver["published_date"],
    )
    return date_results

def company_name_parsing(silver:pd.DataFrame,registry:dict):
    resolved = silver["company_name"].map(
    lambda value: resolve_company(value, registry)
    )
    company_results = pd.DataFrame(
        [asdict(result) for result in resolved],
        index=silver.index,
    )
    company_results = company_results.rename(
        columns={
            "method": "match_method",
            "score": "match_score",
            "candidate": "match_candidate",
        }
    )
    company_results.insert(
        0,
        "company_name_raw",
        silver["company_name"],
    )
    return company_results


def revenue_parsing(silver:pd.DataFrame):
    parsed_revenue = silver["revenue"].map(
    lambda value: parse_revenue(value)
    )
    revenue_results = pd.DataFrame(
        [asdict(result) for result in parsed_revenue],
        index=silver.index,
    )
    revenue_results = revenue_results.rename(
        columns={
            "status": "arr_status",
        }
    )
    revenue_results.insert(
        0,
        "revenue_raw",
        silver["revenue"],
    )
    return revenue_results

def build_source_hash(row: pd.Series) -> str:
    values = [
        row["article_id"],
        row["title"],
        row["summary"],
        row["company_name"],
        row["published_date"],
        row["category"],
        row["revenue"],
        row["url"],
        row["author"],
        row["word_count"],
    ]
    text = "|".join("" if v is None else str(v) for v in values)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_column_order(silver_articles:pd.DataFrame):
    silver_articles = silver_articles[
        [
            "source_file",
            "source_row_num",
            "batch_id",
            "article_id",
            "title",
            "summary",
            "url",
            "author",
            "word_count",
            "published_date_raw",
            "published_date",
            "date_status",
            "date_family",
            "date_convention_used",
            "category_raw",
            "category_std",
            "company_name_raw",
            "company_name",
            "match_method",
            "match_score",
            "match_candidate",
            "revenue_raw",
            "arr_usd",
            "arr_status",
            "parse_method",
            "source_currency",
            "fx_rate_applied",
            "currency_inferred",
            "source_value_hash",
        ]
    ]
    return silver_articles


