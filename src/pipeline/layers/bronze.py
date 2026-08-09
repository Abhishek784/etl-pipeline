from __future__ import annotations
import pandas as pd
from pathlib import Path
from datetime import datetime,timezone
import json


def load_bronze_articles(csv_path: Path, batch_id: str) -> pd.DataFrame :
    df = pd.read_csv(
        csv_path,
        dtype=str,
        keep_default_na=False,
    )
    df["source_file"] = csv_path.name
    df["batch_id"] = batch_id
    df["ingested_at"] = datetime.now(timezone.utc)
    df["source_row_num"] = range(len(df))
    return df


def load_bronze_companies(json_path: Path, batch_id: str) -> pd.DataFrame :
    with open(json_path, "r", encoding="utf-8") as file:
        raw_data = json.load(file)

    rows = []
    for company_name, company_data in raw_data.items():

        row = {
            "company_name": company_name,
            **company_data,
        }

        rows.append(row)
    df = pd.DataFrame(rows)
    df = df.map(lambda v: None if v is None else str(v))
    #df = df.astype(str) # preserve source value as str

    df["source_file"] = json_path.name
    df["source_row_num"] = range(len(df))

    df["batch_id"] = batch_id
    df["ingested_at"] = datetime.now(timezone.utc)
    return df

