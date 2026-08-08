import pytest
from pipeline.cleaning.dates import detect_family,detect_family_conventions, parse_date
from datetime import date

#identifies the date format family.
@pytest.mark.parametrize(
    "raw, expected_family",[
        ("2022-02-17", "iso_date"),
        ("2021-09-11T00:00:00Z", "iso_datetime_z"),
        ("21 Feb 2020", "day_month_year_spaced"),
        ("October 19, 2022", "long_form_comma"),
        ("02/23/2023", "slash_numeric"),
        ("23-08-2023", "dash_numeric_2digit"),
    ],
)
def test_detect_family(raw, expected_family):
    assert detect_family(raw) == expected_family

#identifies the date format family conventions. e.g. whether slash numeric is month first or day first
@pytest.mark.parametrize(
    "raw",[
        "02/23/2023",
        "11/30/2022",
        "01/15/2021",
    ],
)
def test_slash_family_is_month_first(raw):
    conventions = detect_family_conventions([raw])
    assert conventions["slash_numeric"] == "month_first"


@pytest.mark.parametrize(
    "raw", [
        "23-08-2023",
        "15-03-2022",
        "30-12-2020",
    ],
)
def test_dash_family_is_day_first(raw):
    conventions = detect_family_conventions([raw])
    assert conventions["dash_numeric_2digit"] == "day_first"

def test_dash_family_is_split():
    values = [
        "23-08-2023",
        "08-23-2023",
    ]
    conventions = detect_family_conventions(values)
    assert conventions["dash_numeric_2digit"] == "split"


#performs the actual parsing using those inferred conventions and returns both the parsed date and metadata about how it was interpreted.
@pytest.mark.parametrize(
    "raw,expected,status",
    [
        #("04/04/2020", date(2020, 4, 4), "parsed"),
        ("04-05-2021", date(2021, 5, 4), "ambiguous_resolved"),
        ("2022-02-17", date(2022, 2, 17), "parsed"),
        ("21 Feb 2020", date(2020, 2, 21), "parsed"),
        ("October 19, 2022", date(2022, 10, 19), "parsed"),
        ("2021-09-11T00:00:00Z", date(2021, 9, 11), "parsed"),
    ]

)
def test_parse_date(raw, expected, status):
    result = parse_date(raw, detect_family_conventions([raw]))
    assert result.value == expected
    assert result.status == status

#performs the actual parsing using those inferred conventions for ambiguous
@pytest.mark.parametrize(
    "raw,expected,status",
    [
        ("12-10-2021", date(2021, 10, 12), "ambiguous_resolved"),
        ("02-03-2024", date(2024, 3, 2), "ambiguous_resolved"),
    ]
)
def test_parse_date_ambiguous(raw, expected, status):
    conventions = detect_family_conventions([raw])
    result = parse_date(raw, conventions)
    assert result.value == expected
    assert result.status == status