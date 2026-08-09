"""CSV export of the gold layer."""
from __future__ import annotations

from pathlib import Path
import pandas as pd


def export_tables(tables: dict[str, pd.DataFrame], outputs_dir: Path) -> dict[str, Path]:
    """Write each gold table to outputs/<name>.csv. Returns written paths.

    index=False so re-runs don't gain a phantom column; explicit na_rep keeps
    nulls stable across pandas versions, which matters for byte comparison.
    """
    outputs_dir.mkdir(parents=True, exist_ok=True)
    written = {}
    for name, df in tables.items():
        path = outputs_dir / f"{name}.csv"
        df.to_csv(path, index=False, na_rep="")
        written[name] = path
    return written