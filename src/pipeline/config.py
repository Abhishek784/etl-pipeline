"""Configuration loading.

The cleaning modules take plain dicts, never file paths -- that is what keeps
them unit-testable with a literal fixture and free of IO. This module is the
only place in the pipeline that reads config off disk.

Paths resolve relative to the project root (the directory containing
pyproject.toml), so `make run` and `pytest` behave the same regardless of the
working directory they are invoked from.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


def project_root() -> Path:
    """Walk upwards from this file until pyproject.toml is found."""
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "pyproject.toml").exists():
            return candidate
    # Installed without the source tree alongside: fall back to CWD.
    return Path.cwd()


def resolve(relative: str | Path) -> Path:
    """Turn a config-relative path into an absolute one."""
    path = Path(relative)
    return path if path.is_absolute() else project_root() / path


def _read_yaml(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if data is None:
        raise ValueError(f"Config file is empty: {path}")
    return data


@lru_cache(maxsize=None)
def load_settings(path: str = "config/settings.yaml") -> dict:
    """FX rates, thresholds, size bands, and file paths."""
    settings = _read_yaml(resolve(path))

    required = {"paths", "fx_rates", "company_matching", "company_size_bands", "ai_export"}
    missing = required - settings.keys()
    if missing:
        raise ValueError(f"settings.yaml missing required sections: {sorted(missing)}")

    return settings


@lru_cache(maxsize=None)
def load_category_map(path: str = "config/category_map.yaml") -> dict[str, tuple[str, ...]]:
    """canonical_code -> variants, as authored. Inversion happens in
    build_category_lookup, which owns the duplicate check."""
    raw = _read_yaml(resolve(path))

    if not isinstance(raw, dict):
        raise ValueError("category_map.yaml must be a mapping of code -> [variants]")

    # tuples so the lru_cache result cannot be mutated by a caller
    return {code: tuple(variants) for code, variants in raw.items()}


@lru_cache(maxsize=None)
def load_company_aliases(path: str = "config/company_aliases.yaml") -> dict[str, str]:
    """raw_name -> canonical metadata key."""
    raw = _read_yaml(resolve(path))

    if not isinstance(raw, dict):
        raise ValueError("company_aliases.yaml must be a mapping of alias -> canonical name")

    for alias, target in raw.items():
        if not isinstance(target, str) or not target.strip():
            raise ValueError(f"Alias {alias!r} has an empty or non-string target")

    return dict(raw)


@lru_cache(maxsize=None)
def load_company_metadata(path: str | None = None) -> dict[str, dict]:
    """canonical_name -> metadata fields, straight from the source JSON."""
    resolved = resolve(path or load_settings()["paths"]["raw_metadata"])

    if not resolved.exists():
        raise FileNotFoundError(f"Company metadata not found: {resolved}")

    with resolved.open("r", encoding="utf-8") as handle:
        metadata = json.load(handle)

    if not isinstance(metadata, dict):
        raise ValueError("company_metadata.json must be an object keyed by company name")

    expected = {"founded_year", "headquarters", "employee_count",
                "industry", "is_public", "stock_ticker"}
    for name, fields in metadata.items():
        missing = expected - fields.keys()
        if missing:
            raise ValueError(f"Company {name!r} missing fields: {sorted(missing)}")

    return metadata


def lossy_aliases(settings: dict | None = None) -> set[str]:
    """Aliases whose resolution loses information (product -> parent, or two
    entities collapsed into one). Flagged so the judgement stays visible."""
    settings = settings or load_settings()
    return set(settings.get("company_matching", {}).get("lossy_aliases", []))