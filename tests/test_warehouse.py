from __future__ import annotations

import pytest

duckdb = pytest.importorskip("duckdb")

from pipeline.config import resolve
from pipeline.warehouse.loader import PRIMARY_KEYS, load_warehouse


@pytest.fixture
def db(tmp_path):
    return tmp_path / "arr.duckdb"


@pytest.fixture
def sql_paths():
    return (
        resolve("src/pipeline/warehouse/schema.sql"),
        resolve("src/pipeline/warehouse/views.sql"),
    )


def test_first_load_writes_expected_counts(gold_tables, db, sql_paths):
    counts = load_warehouse(gold_tables, db, *sql_paths)
    assert counts["dim_company"] == 21
    assert counts["dim_article"] == 750
    assert counts["fact_arr_observation"] == 538
    assert counts["quarantine_record"] == 217


def test_second_load_does_not_duplicate(gold_tables, db, sql_paths):
    """The whole point. Append semantics would double every table here."""
    first = load_warehouse(gold_tables, db, *sql_paths)
    second = load_warehouse(gold_tables, db, *sql_paths)
    assert first == second


def test_restated_value_updates_in_place(gold_tables, db, sql_paths):
    """A corrected figure keeps its key and overwrites -- it does not insert."""
    load_warehouse(gold_tables, db, *sql_paths)

    fact = gold_tables["fact_arr_observation"].copy()
    target = fact.iloc[0]["arr_observation_id"]
    fact.loc[fact.arr_observation_id == target, "arr_usd"] = 999_000_000

    counts = load_warehouse({**gold_tables, "fact_arr_observation": fact}, db, *sql_paths)
    assert counts["fact_arr_observation"] == 538

    with duckdb.connect(str(db)) as con:
        value = con.execute(
            "SELECT arr_usd FROM fact_arr_observation WHERE arr_observation_id = ?",
            [target],
        ).fetchone()[0]
    assert value == 999_000_000


def test_views_return_one_row_per_company(gold_tables, db, sql_paths):
    load_warehouse(gold_tables, db, *sql_paths)
    with duckdb.connect(str(db)) as con:
        rows = con.execute(
            "SELECT company_key, count(*) FROM vw_company_arr_latest GROUP BY 1 HAVING count(*) > 1"
        ).fetchall()
    assert rows == [], "latest view must collapse to one row per company"


def test_conflicting_same_day_observations_are_reported(gold_tables, db, sql_paths):
    """Six company-date pairs disagree. The view must surface that, not hide it."""
    load_warehouse(gold_tables, db, *sql_paths)
    with duckdb.connect(str(db)) as con:
        contested = con.execute(
            "SELECT count(*) FROM vw_company_arr_latest WHERE observation_count_on_date > 1"
        ).fetchone()[0]
    assert contested >= 1


def test_check_constraint_rejects_nonpositive_arr(gold_tables, db, sql_paths):
    load_warehouse(gold_tables, db, *sql_paths)
    fact = gold_tables["fact_arr_observation"].copy()
    fact.loc[fact.index[0], "arr_usd"] = 0
    with pytest.raises(Exception):
        load_warehouse({**gold_tables, "fact_arr_observation": fact}, db, *sql_paths)