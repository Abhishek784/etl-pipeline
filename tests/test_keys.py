from __future__ import annotations

import os
import subprocess
import sys

import pytest

from pipeline.keys import (
    KEY_LENGTH,
    arr_observation_key,
    article_key,
    company_key,
    normalise_name,
    quarantine_key,
    source_value_hash,
)


class TestNormaliseName:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("Amazon Web Services", "amazonwebservices"),
            ("  Snowflake  ", "snowflake"),
            ("Mongo DB", "mongodb"),
            ("NVIDIA", "nvidia"),
            ("Scale AI", "scaleai"),
            ("The Boring Company / SpaceX", "theboringcompanyspacex"),
        ],
    )
    def test_normalises(self, raw: str, expected: str) -> None:
        assert normalise_name(raw) == expected

    def test_case_and_spacing_converge(self) -> None:
        assert normalise_name("Google DeepMind") == normalise_name("google deepmind")


class TestKeyShape:
    def test_all_keys_are_fixed_length_lowercase_hex(self) -> None:
        keys = [
            company_key("Snowflake"),
            article_key("ART0001"),
            arr_observation_key("ART0001"),
            quarantine_key("tech_news.csv", 42, "arr_parse"),
            source_value_hash("$5.2B"),
        ]
        for key in keys:
            assert len(key) == KEY_LENGTH
            assert key == key.lower()
            assert all(c in "0123456789abcdef" for c in key)


class TestDeterminism:
    def test_same_input_same_key(self) -> None:
        assert company_key("Snowflake") == company_key("Snowflake")
        assert article_key("ART0042") == article_key("ART0042")

    def test_different_input_different_key(self) -> None:
        assert company_key("Snowflake") != company_key("Databricks")
        assert article_key("ART0001") != article_key("ART0002")

    def test_namespaces_do_not_collide(self) -> None:
        """Same input in different key families must not produce the same key."""
        assert article_key("ART0001") != arr_observation_key("ART0001")

    def test_no_delimiter_collision(self) -> None:
        """('ab','c') and ('a','bc') must not collide."""
        assert quarantine_key("ab", 1, "c") != quarantine_key("a", 1, "bc")


class TestRestatementDetection:
    def test_observation_key_ignores_the_value(self) -> None:
        """A corrected figure keeps the same key -- the merge updates in place."""
        assert arr_observation_key("ART0042") == arr_observation_key("ART0042")

    def test_value_hash_detects_the_change(self) -> None:
        assert source_value_hash("$5.2B") != source_value_hash("$5.4B")

    def test_value_hash_ignores_surrounding_whitespace(self) -> None:
        assert source_value_hash("  $5.2B ") == source_value_hash("$5.2B")

    def test_none_and_empty_agree(self) -> None:
        assert source_value_hash(None) == source_value_hash("")


class TestRejectsEmptyInput:
    @pytest.mark.parametrize("bad", ["", "   "])
    def test_company_key_rejects_blank(self, bad: str) -> None:
        with pytest.raises(ValueError):
            company_key(bad)

    @pytest.mark.parametrize("bad", ["", "   "])
    def test_article_key_rejects_blank(self, bad: str) -> None:
        with pytest.raises(ValueError):
            article_key(bad)


_SUBPROCESS_SNIPPET = """
import sys
sys.path.insert(0, {src!r})
from pipeline.keys import company_key, article_key, arr_observation_key
print(company_key("Snowflake"))
print(article_key("ART0042"))
print(arr_observation_key("ART0042"))
"""


def test_keys_are_stable_across_processes_and_hash_seeds() -> None:
    src = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")
    expected = [company_key("Snowflake"), article_key("ART0042"), arr_observation_key("ART0042")]

    env = {**os.environ, "PYTHONHASHSEED": "12345"}
    result = subprocess.run(
        [sys.executable, "-c", _SUBPROCESS_SNIPPET.format(src=src)],
        capture_output=True, text=True, env=env,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == expected
    assert result.stdout.split() == expected