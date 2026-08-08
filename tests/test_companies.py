from pipeline.cleaning.companies import resolve_company
from pipeline.cleaning.companies import build_registry, normalise_company_name
import pytest

@pytest.fixture
def registry():
    return build_registry(
        [
            "OpenAI",
            "NVIDIA",
            "MongoDB",
            "Stripe",
            "Palantir",
            "Amazon Web Services",
            "Google DeepMind",
            "Meta AI",
            "Microsoft",
            "SpaceX",
        ],
        aliases={
            "AWS": "Amazon Web Services",
            "DeepMind": "Google DeepMind",
            "Facebook AI Research": "Meta AI",
            "Azure": "Microsoft",
            "The Boring Company / SpaceX": "SpaceX",
        },
        lossy_aliases={
            "Azure",
            "The Boring Company / SpaceX",
        },
    )

#test_resolve_company
@pytest.mark.parametrize(
    "raw, expected_company, expected_method",
    [
        # Exact
        ("OpenAI", "OpenAI", "exact"),
        ("NVIDIA", "NVIDIA", "exact"),

        # Normalised
        ("Nvidia", "NVIDIA", "normalized"),       # case
        ("Mongo DB", "MongoDB", "normalized"),    # spacing
        ("Stripe Inc.", "Stripe", "normalized"),  # suffix
        ("Palantir Technologies", "Palantir", "normalized"),

        # Alias
        ("AWS", "Amazon Web Services", "alias"),
        ("DeepMind", "Google DeepMind", "alias"),
        ("Facebook AI Research", "Meta AI", "alias"),

        # Lossy alias
        ("Azure", "Microsoft", "alias_lossy"),
        ("The Boring Company / SpaceX", "SpaceX", "alias_lossy"),

        # No match
        ("Cohere", None, "no_match"),
        ("xAI", None, "no_match"),
    ],
)
def test_resolve_company(registry, raw, expected_company, expected_method):
    result = resolve_company(raw, registry)

    assert result.company_name == expected_company
    assert result.method == expected_method



#test_normalise_company_name
@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Nvidia", "nvidia"),
        ("NVIDIA Corporation", "nvidia"),
        ("Mongo DB", "mongodb"),
        ("Stripe Inc.", "stripe"),
        ("Palantir Technologies", "palantir"),
    ],
)
def test_normalise_company_name(raw, expected):
    assert normalise_company_name(raw) == expected