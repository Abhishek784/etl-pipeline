import pytest
from pipeline.cleaning.revenue import parse_revenue

@pytest.mark.parametrize(("raw", "expected_usd", "method"), [
    ("$5.2B",              5_200_000_000, "single"),
    ("$980.0M",              980_000_000, "single"),
    ("$5.2 billion",       5_200_000_000, "single"),
    ("5.2M USD",               5_200_000, "single"),
    ("$5,200,000,000",     5_200_000_000, "single"),
    ("$10.0M - $20.0M",       15_000_000, "range_midpoint"),
    ("€2,100,000,000",     2_310_000_000, "single"),   # x1.1
    ("£1,000,000,000",     1_270_000_000, "single"),   # x1.27
    ("¥300,000,000,000",   2_000_000_000, "single"),   # /150
])
def test_parses(raw, expected_usd, method):
    result = parse_revenue(raw)
    assert result.status == "ok"
    assert result.arr_usd == expected_usd
    assert result.parse_method == method


@pytest.mark.parametrize("raw", [None, float("nan"), "", "   ", "N/A", "n/a", "-"])
def test_missing(raw):
    assert parse_revenue(raw).status == "missing"
    assert parse_revenue(raw).arr_usd is None


@pytest.mark.parametrize("raw", ["Not disclosed", "not disclosed", "  Not Disclosed  "])
def test_not_disclosed(raw):
    result = parse_revenue(raw)
    assert result.status == "not_disclosed"
    assert result.arr_usd is None



def test_garbage_does_not_raise():
    assert parse_revenue("about five bucks").status == "unparseable"


def test_currency_metadata():
    r = parse_revenue("€2,100,000,000")
    assert r.source_currency == "EUR"
    assert r.fx_rate_applied == 1.1
    assert r.currency_inferred is True




def test_jpy_rate_is_division_not_multiplication():
    r = parse_revenue("¥300,000,000,000")
    assert r.source_currency == "JPY"
    assert r.fx_rate_applied == pytest.approx(1 / 150)


def test_range_midpoint_taken_before_conversion():
    r = parse_revenue("$10.0M - $20.0M")
    assert r.parse_method == "range_midpoint"
    assert r.fx_rate_applied == 1.0


def test_failure_branches_have_no_currency():
    for raw in (None, "N/A", "Not disclosed", "about five bucks"):
        r = parse_revenue(raw)
        assert r.source_currency is None
        assert r.fx_rate_applied is None
        assert r.currency_inferred is False