from __future__ import annotations

import hashlib
import re

KEY_LENGTH = 16

_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_WHITESPACE = re.compile(r"\s+")


def _digest(*parts: str) -> str:
    #Hash the given parts into a stable lowercase hex key.
    payload = "\x1f".join(parts).encode("utf-8")
    return hashlib.md5(payload).hexdigest()[:KEY_LENGTH]


def normalise_name(name: str) -> str:
    lowered = _WHITESPACE.sub(" ", name.strip().lower())
    return _NON_ALNUM.sub("", lowered)


def company_key(canonical_name: str) -> str:
    """Key for a resolved company. Input must be the canonical metadata key."""
    if not canonical_name or not canonical_name.strip():
        raise ValueError("company_key requires a non-empty canonical name")
    return _digest("company", normalise_name(canonical_name))


def article_key(article_id: str) -> str:
    """Key for a source article."""
    if not article_id or not article_id.strip():
        raise ValueError("article_key requires a non-empty article_id")
    return _digest("article", article_id.strip())


def arr_observation_key(article_id: str) -> str:
    if not article_id or not article_id.strip():
        raise ValueError("arr_observation_key requires a non-empty article_id")
    return _digest("arr_obs", article_id.strip())


def quarantine_key(source_file: str, row_num: int, stage: str) -> str:
    return _digest("quarantine", source_file, str(row_num), stage)


def source_value_hash(raw_value: str | None) -> str:
    return _digest("value", "" if raw_value is None else raw_value.strip())