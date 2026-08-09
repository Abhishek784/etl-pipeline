from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

PRIMARY_KEYS = {
    "dim_company": "company_key",
    "dim_article": "article_sk",
    "fact_arr_observation": "arr_observation_id",
    "quarantine_record": "quarantine_id",
}

AUDIT_COLUMNS = {"updated_at"}


def connect(db_path: Path) -> duckdb.DuckDBPyConnection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path))


def apply_sql_file(con: duckdb.DuckDBPyConnection, path: Path) -> None:
    con.execute(path.read_text(encoding="utf-8"))


def _to_duckdb_safe(df: pd.DataFrame) -> pd.DataFrame:
    """Convert pandas nullable extension dtypes (Int64, boolean) to object with
    real None values. DuckDB's pandas bridge handles NumPy and object columns
    reliably; pd.NA in an extension array can surface as a type error.
    """
    out = df.copy()
    for col in out.columns:
        if str(out[col].dtype) in {"Int64", "boolean", "Float64", "string"}:
            out[col] = out[col].astype(object).where(out[col].notna(), None)
    return out


def merge_table(
    con: duckdb.DuckDBPyConnection,
    table: str,
    df: pd.DataFrame,
    primary_key: str,
) -> int:
    """Upsert a DataFrame into `table`, keyed on `primary_key`.

    Returns the resulting row count in the table.
    """
    if df.empty:
        return con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]

    staged = _to_duckdb_safe(df)
    con.register("_staging", staged)

    columns = list(staged.columns)
    col_list = ", ".join(f'"{c}"' for c in columns)

    updatable = [c for c in columns if c != primary_key and c not in AUDIT_COLUMNS]
    set_clause = ", ".join(f'"{c}" = excluded."{c}"' for c in updatable)

    # Touch updated_at only on tables that carry it.
    has_updated_at = "updated_at" in {
        r[0] for r in con.execute(f"DESCRIBE {table}").fetchall()
    }
    if has_updated_at:
        set_clause += ', "updated_at" = current_localtimestamp()'
    
    con.execute(
        f"""
        INSERT INTO {table} ({col_list})
        SELECT {col_list} FROM _staging
        ON CONFLICT ("{primary_key}") DO UPDATE SET {set_clause}
        """
    )
    con.unregister("_staging")
    return con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


def load_warehouse(
    tables: dict[str, pd.DataFrame],
    db_path: Path,
    schema_sql: Path,
    views_sql: Path,
) -> dict[str, int]:
    """Create schema if needed, merge every known table, then refresh views.

    dim_company loads first so the fact table's foreign keys resolve.
    """
    counts: dict[str, int] = {}
    with connect(db_path) as con:
        apply_sql_file(con, schema_sql)

        order = ["dim_company", "dim_article", "fact_arr_observation", "quarantine_record"]
        for name in order:
            if name in tables:
                counts[name] = merge_table(con, name, tables[name], PRIMARY_KEYS[name])

        apply_sql_file(con, views_sql)
    return counts