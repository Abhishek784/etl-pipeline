from __future__ import annotations
from pipeline.cli import run_pipeline

import pandas as pd
import pytest

AUDIT_COLUMNS = {"batch_id", "ingested_at"}


def _business_content(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns=[c for c in df.columns if c in AUDIT_COLUMNS])


@pytest.fixture(scope="module")
def two_runs():
    first  = run_pipeline(batch_id="BATCH_001")
    second = run_pipeline(batch_id="BATCH_002")
    return first.gold_tables, second.gold_tables


def test_same_tables_produced(two_runs):
    first, second = two_runs
    assert set(first) == set(second)


def test_row_counts_unchanged(two_runs):
    """A rerun must not append duplicates."""
    first, second = two_runs
    for name in first:
        assert len(first[name]) == len(second[name]), f"{name} changed row count"


def test_primary_keys_identical(two_runs):
    """Content hashes must not depend on run order, time, or batch."""
    first, second = two_runs
    pks = {
        "dim_company": "company_key",
        "dim_article": "article_sk",
        "fact_arr_observation": "arr_observation_id",
        "quarantine_record": "quarantine_id",
    }
    for name, pk in pks.items():
        assert list(first[name][pk]) == list(second[name][pk]), f"{name}.{pk} unstable"


def test_business_content_identical(two_runs):
    """Everything except audit metadata must match exactly."""
    first, second = two_runs
    for name in first:
        pd.testing.assert_frame_equal(
            _business_content(first[name]),
            _business_content(second[name]),
            check_like=False,
        )


def test_csv_export_is_byte_identical(two_runs, tmp_path):
    """The deliverable itself, not just the in-memory frames."""
    from pipeline.exports import export_tables
    first, second = two_runs
    a = export_tables({k: _business_content(v) for k, v in first.items()}, tmp_path / "a")
    b = export_tables({k: _business_content(v) for k, v in second.items()}, tmp_path / "b")
    for name in a:
        assert a[name].read_bytes() == b[name].read_bytes(), f"{name}.csv differs"