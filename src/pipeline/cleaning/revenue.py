from dataclasses import dataclass
import math

FX_RATES = {
    "$": 1.0,
    "€": 1.10,
    "£": 1.27,
    "¥": 1 / 150,
}

@dataclass
class RevenueParseResult:
    status: str
    arr_usd: int | None
    parse_method: str | None


def parse_revenue(raw: str):
    """Parse revenue string into USD.
    """
    if raw is None:
        return RevenueParseResult(
            status="missing",
            arr_usd=None,
            parse_method=None
        )

    if isinstance(raw, float) and math.isnan(raw):
        return RevenueParseResult(
            status="missing",
            arr_usd=None,
            parse_method=None
        )

    if isinstance(raw, str) and raw.strip() == "":
        return RevenueParseResult(
            status="missing",
            arr_usd=None,
            parse_method=None
        )
    
    # Not disclosed values
    if isinstance(raw, str):
        normalized = raw.strip().lower()

        if normalized in {"not disclosed", "n/a"}:
            return RevenueParseResult(
                status="not_disclosed",
                arr_usd=None,
                parse_method=None
            )
    try:
        if " - " in raw:
            left, right = raw.split(" - ")

            left_value = parse_single(left)
            right_value = parse_single(right)

            expected_usd = round((left_value + right_value) / 2)
            method = "range_midpoint"
        else:
            expected_usd = round(parse_single(raw))
            method = "single"
        if raw is None:
            return RevenueParseResult(
                status="missing",
                arr_usd=None,
                parse_method="none"
            )
    except Exception:
        return RevenueParseResult(
            status="unparseable",
            arr_usd=None,
            parse_method=None
        )
    return RevenueParseResult(
        status="ok",
        arr_usd=expected_usd,
        parse_method=method
    )

def parse_single(value: str) -> float:
    value = value.strip()

    currency = "$"

    if value.startswith("€"):
        currency = "€"
        value = value[1:]

    elif value.startswith("£"):
        currency = "£"
        value = value[1:]

    elif value.startswith("¥"):
        currency = "¥"
        value = value[1:]

    elif value.startswith("$"):
        currency = "$"
        value = value[1:]

    elif value.upper().endswith("USD"):
        value = value[:-3].strip()

    value = value.replace(",", "").strip()

    lower = value.lower()

    multiplier = 1

    if lower.endswith("billion"):
        multiplier = 1_000_000_000
        value = value[:-7].strip()

    elif lower.endswith("million"):
        multiplier = 1_000_000
        value = value[:-7].strip()

    elif lower.endswith("b"):
        multiplier = 1_000_000_000
        value = value[:-1].strip()

    elif lower.endswith("m"):
        multiplier = 1_000_000
        value = value[:-1].strip()

    return float(value) * multiplier * FX_RATES[currency]
