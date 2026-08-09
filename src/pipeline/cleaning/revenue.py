from dataclasses import dataclass
import math

FX_RATES = {"USD": 1.0, "EUR": 1.10, "GBP": 1.27, "JPY": 1 / 150}
SYMBOL_TO_ISO = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY"}

@dataclass
class RevenueParseResult:
    status: str
    arr_usd: int | None
    parse_method: str | None
    source_currency: str | None      # "USD" | "EUR" | "GBP" | "JPY"
    fx_rate_applied: float | None
    currency_inferred: bool


def parse_revenue(raw: str):
    """Parse revenue string into USD.
    """
    if raw is None:
        return RevenueParseResult(
            status="missing",
            arr_usd=None,
            parse_method=None,
            source_currency=None,
            fx_rate_applied=None,
            currency_inferred=False 
        )

    if isinstance(raw, float) and math.isnan(raw):
        return RevenueParseResult(
            status="missing",
            arr_usd=None,
            parse_method=None,
            source_currency=None,
            fx_rate_applied=None,
            currency_inferred=False
        )

    if isinstance(raw, str) and raw.strip() == "":
        return RevenueParseResult(
            status="missing",
            arr_usd=None,
            parse_method=None,
            source_currency=None,
            fx_rate_applied=None,
            currency_inferred=False
        )
    
    # Not disclosed values
    if isinstance(raw, str):
        normalized = raw.strip().lower()

        if normalized in {"", "n/a", "na", "none", "null", "-"}:
            return RevenueParseResult(
                status="missing",
                arr_usd=None,
                parse_method=None,
                source_currency=None,
                fx_rate_applied=None,
                currency_inferred=False
            )   

        if normalized in {"not disclosed", "undisclosed"}:
            return RevenueParseResult(
                status="not_disclosed",
                arr_usd=None,
                parse_method=None,  
                source_currency=None,
                fx_rate_applied=None,
                currency_inferred=False
            )
    try:
        if " - " in raw:
            left, right = raw.split(" - ")

            left_value,currency = parse_single(left)
            right_value,currency = parse_single(right)

            expected_usd = round((left_value + right_value) / 2)
            method = "range_midpoint"
        else:
            expected_usd,currency = parse_single(raw)
            expected_usd = round(expected_usd)
            method = "single"
        if raw is None:
            return RevenueParseResult(
                status="missing",
                arr_usd=None,
                parse_method="none",
                source_currency=None,
                fx_rate_applied=None,
                currency_inferred=False
            )
    except Exception:
        return RevenueParseResult(
            status="unparseable",
            arr_usd=None,
            parse_method=None,
            source_currency=None,
            fx_rate_applied=None,
            currency_inferred=False
        )
    return RevenueParseResult(
        status="ok",
        arr_usd=expected_usd,
        parse_method=method,
        source_currency=currency,
        fx_rate_applied=FX_RATES[currency],
        currency_inferred=True
    )

def parse_single(value: str) -> tuple[float,str]:
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
    iso=SYMBOL_TO_ISO[currency]
    return float(value) * multiplier * FX_RATES[iso], iso