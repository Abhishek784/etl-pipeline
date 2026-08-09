from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import argparse, json
import pandas as pd

from pipeline.layers import bronze, silver, gold
from pipeline.cleaning.categories import build_category_lookup
from pipeline.cleaning.companies import build_registry
from pipeline.config import (
    load_settings, load_category_map, load_company_aliases, load_company_metadata,
)
from pipeline.exports import export_tables


@dataclass
class PipelineResult:
    silver_articles: pd.DataFrame
    silver_companies: pd.DataFrame
    gold_tables: dict[str, pd.DataFrame]
    batch_id: str


def run_pipeline(batch_id: str | None = None, skip_embeddings: bool = False) -> PipelineResult:
    batch_id = batch_id or datetime.now(timezone.utc).strftime("BATCH_%Y%m%dT%H%M%S")

    settings   = load_settings()
    lookup     = build_category_lookup(load_category_map())
    metadata   = load_company_metadata()
    registry   = build_registry(
        list(metadata),
        aliases=load_company_aliases(),
        lossy_aliases=set(settings.get("lossy_aliases", [])),
    )

    paths = settings["paths"]
    b_articles  = bronze.load_bronze_articles(Path(paths["raw_articles"]), batch_id)
    b_companies = bronze.load_bronze_companies(Path(paths["raw_metadata"]), batch_id)

    s_companies = silver.build_silver_companies(b_companies, lookup)
    s_articles  = silver.build_column_order(
        silver.build_silver_articles(b_articles, registry, lookup)
    )

    dim_company = gold.build_dim_companies(s_companies, settings)
    tables = {
        "dim_company": dim_company,
        "dim_article": gold.build_dim_articles(s_articles),
        "fact_arr_observation": gold.build_fact_arr_observation(s_articles, dim_company, batch_id),
        "quarantine_record": gold.build_quarantine_record(s_articles, batch_id),
    }

    return PipelineResult(s_articles, s_companies, tables, batch_id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Tech-news ARR pipeline")
    parser.add_argument("--batch-id", default=None)
    parser.add_argument("--skip-embeddings", action="store_true")
    args = parser.parse_args()

    result = run_pipeline(args.batch_id, args.skip_embeddings)
    written = export_tables(result.gold_tables, Path("outputs"))
    for name, path in written.items():
        print(f"{name:24} {len(result.gold_tables[name]):>5} rows -> {path}")


if __name__ == "__main__":
    main()