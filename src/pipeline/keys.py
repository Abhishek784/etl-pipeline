"""Deterministic surrogate keys.

Every key in this pipeline is a content hash, never a sequence. This is what
makes gold loads MERGE-able and reruns idempotent: the same source row always
computes the same key, in this process or any other, today or in six months.

Do not use the ``hash()`` builtin anywhere in this module. It is salted per
process via PYTHONHASHSEED, so it produces different values across runs --
which would silently break the idempotency guarantee. ``test_keys.py`` asserts
this by running under a different seed in a subprocess.
"""

from __future__ import annotations

import hashlib
import re

KEY_LENGTH = 16

_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_WHITESPACE = re.compile(r"\s+")


def _digest(*parts: str) -> str:
    """Hash the given parts into a stable lowercase hex key.

    Parts are joined with a delimiter that cannot appear in a normalised
    name, so ("ab", "c") and ("a", "bc") never collide.
    """
    payload = "\x1f".join(parts).encode("utf-8")
    return hashlib.md5(payload).hexdigest()[:KEY_LENGTH]


def normalise_name(name: str) -> str:
    """Lowercase, collapse whitespace, strip non-alphanumerics.

    Used only for key generation. Suffix stripping (Inc, Ltd, ...) belongs in
    cleaning.companies, not here -- this function must stay stable forever,
    because changing it changes every company_key ever issued.
    """
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
    """Key for an ARR observation.

    Grain is one observation per article, so article_id alone determines the
    key. The revenue value is deliberately NOT part of the key: if an article
    is re-ingested with a corrected figure, we want the merge to update the
    existing row rather than insert a second one. Use source_value_hash to
    detect that the value changed.
    """
    if not article_id or not article_id.strip():
        raise ValueError("arr_observation_key requires a non-empty article_id")
    return _digest("arr_obs", article_id.strip())


def quarantine_key(source_file: str, row_num: int, stage: str) -> str:
    """Key for a quarantined value.

    Includes stage so one source row failing at two stages (e.g. bad date AND
    unmatched company) produces two distinct quarantine rows rather than
    colliding into one.
    """
    return _digest("quarantine", source_file, str(row_num), stage)


def source_value_hash(raw_value: str | None) -> str:
    """Fingerprint of a raw source value, for restatement detection.

    A re-ingested article whose revenue string changed keeps the same
    observation key but gets a different value hash, so the loader can tell
    "same row again" from "upstream corrected it" and bump updated_at.
    """
    return _digest("value", "" if raw_value is None else raw_value.strip())