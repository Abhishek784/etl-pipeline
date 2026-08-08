
from dataclasses import dataclass
from datetime import date
import re
from collections import defaultdict
from datetime import datetime

FAMILY_PATTERNS = {
    "iso_date": re.compile(r"^\d{4}-\d{2}-\d{2}$"),
    "iso_datetime_z": re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"),
    "day_month_year_spaced": re.compile(r"^\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}$"),
    "long_form_comma": re.compile(r"^[A-Za-z]{3,9}\s+\d{1,2},\s+\d{4}$"),
    "slash_numeric": re.compile(r"^\d{1,2}/\d{1,2}/\d{4}$"),
    "dash_numeric_2digit": re.compile(r"^\d{1,2}-\d{1,2}-\d{4}$"),
}

@dataclass
class DateParseResult:
    value: date | None
    status: str
    family: str
    convention_used: str | None
    



def detect_family(raw:str) -> str:
    if raw is None:
        return None
    raw = raw.strip()
    for family, pattern in FAMILY_PATTERNS.items():
        if pattern.fullmatch(raw):
            return family
    return None
    
def detect_family_conventions(values: list[str]) -> dict[str,str]:

    evidence = defaultdict(lambda: {"month_first": 0, "day_first": 0})

    for raw in values:
        family = detect_family(raw)
        if family not in {"slash_numeric", "dash_numeric_2digit"}:
            continue
        sep = "/" if "/" in raw else "-"
        first, second, _ = raw.split(sep)
        first = int(first)
        second = int(second)
        # 23/08/2023
        if first > 12 and second <= 12:
            evidence[family]["day_first"] += 1
        # 08/23/2023
        elif second > 12 and first <= 12:
            evidence[family]["month_first"] += 1

    conventions = {}

    for family, counts in evidence.items():
        d = counts["day_first"]
        m = counts["month_first"]
        if d == 0 and m == 0:
            conventions[family] = "split"
        elif d > 0 and m == 0:
            conventions[family] = "day_first"
        elif m > 0 and d == 0:
            conventions[family] = "month_first"
        else:
            conventions[family] = "split"

    return conventions


def parse_date(raw: str, conventions: dict[str,str]) -> DateParseResult:
    family = detect_family(raw)

    if family is None:
        return DateParseResult(
            value=None,
            status="invalid",
            family=None,
            convention_used=None,
        )

    if family == "iso_date":

        return DateParseResult(
            datetime.strptime(raw, "%Y-%m-%d").date(),
            "parsed",
            family,
            None,
        )
    if family == "iso_datetime_z":

        # Explicitly strip the Z
        raw = raw[:-1]

        return DateParseResult(
            datetime.strptime(raw, "%Y-%m-%dT%H:%M:%S").date(),
            "parsed",
            family,
            None,
        )

    if family == "day_month_year_spaced":

        return DateParseResult(
            datetime.strptime(raw, "%d %b %Y").date(),
            "parsed",
            family,
            None,
        )

    if family == "long_form_comma":

        return DateParseResult(
            datetime.strptime(raw, "%B %d, %Y").date(),
            "parsed",
            family,
            None,
        )

    return parse_numeric(raw, family, conventions)

def parse_numeric(raw, family, conventions):

    sep = "/" if "/" in raw else "-"

    first, second, year = raw.split(sep)

    first = int(first)
    second = int(second)
    year = int(year)

    # obvious day first
    if first > 12:
        return DateParseResult(
            date(year, second, first),
            "parsed",
            family,
            "day_first",
        )

    # obvious month first
    if second > 12:
        return DateParseResult(
            date(year, first, second),
            "parsed",
            family,
            "month_first",
        )

    convention = conventions.get(family, "split")

    if convention == "day_first":

        return DateParseResult(
            date(year, second, first),
            "parsed",
            family,
            convention,
        )

    if convention == "month_first":

        return DateParseResult(
            date(year, first, second),
            "parsed",
            family,
            convention,
        )

    # Split → default to day-first but record reduced confidence
    return DateParseResult(
        date(year, second, first),
        "ambiguous_resolved",
        family,
        "split",
    )