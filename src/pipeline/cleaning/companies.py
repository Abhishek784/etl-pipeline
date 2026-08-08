import re
from dataclasses import dataclass
from difflib import SequenceMatcher



# CompanyRegistry as  in-memory lookup database.
@dataclass
class CompanyRegistry:
    exact: dict[str, str]
    normalized: dict[str, str]
    aliases: dict[str, str]
    lossy_aliases: set[str]

@dataclass
class CompanyMatch:
    company_name: str | None
    method: str
    score: float | None = None


_SUFFIXES = [
    "inc.",
    "inc",
    "corporation",
    "corp.",
    "corp",
    "technologies",
    "technology",
    "limited",
    "ltd.",
    "ltd",
    "llc",
    "plc",
]

_SUFFIX_RE = re.compile(
    r"\s+(?:"
    + "|".join(re.escape(s) for s in sorted(_SUFFIXES, key=len, reverse=True))
    + r")\s*$",
    flags=re.IGNORECASE,
)


def normalise_company_name(raw: str) -> str:
    if raw is None:
        return ""
    value = raw.strip().lower()
    value = _SUFFIX_RE.sub("", value)     # Remove one suffix at the end
    value = re.sub(r"[^a-z0-9]", "", value) # Remove punctuation, spaces, slashes, hyphens, etc.

    return value

companies = [
    "OpenAI",
    "NVIDIA",
    "Google DeepMind",
    "MongoDB",
    "Stripe",
]

def build_registry(
    company_names: list[str],
    aliases: dict[str, str] | None = None,
    lossy_aliases: set[str] | None = None,
) -> CompanyRegistry:

    aliases = aliases or {}
    lossy_aliases = lossy_aliases or set()

    exact = {}
    normalized = {}

    for company_name in company_names:

        # Exact lookup
        exact[company_name] = company_name

        # Normalised lookup
        key = normalise_company_name(company_name)
        normalized[key] = company_name

    return CompanyRegistry(
        exact=exact,
        normalized=normalized,
        aliases=aliases,
        lossy_aliases=lossy_aliases,
    )

def resolve_exact(
    raw: str,
    registry: CompanyRegistry,
) -> CompanyMatch | None:

    if raw in registry.exact:
        return CompanyMatch(
            company_name=registry.exact[raw],
            method="exact",
        )

    return None

def resolve_normalised(
    raw: str,
    registry: CompanyRegistry,
) -> CompanyMatch | None:

    key = normalise_company_name(raw)

    if not key:
        return None

    if key in registry.normalized:
        return CompanyMatch(
            company_name=registry.normalized[key],
            method="normalized",
        )

    return None

def resolve_alias(
    raw: str,
    registry: CompanyRegistry,
) -> CompanyMatch | None:

    if raw not in registry.aliases:
        return None
    company_name = registry.aliases[raw]
    method = (
        "alias_lossy"
        if raw in registry.lossy_aliases
        else "alias"
    )

    return CompanyMatch(
        company_name=company_name,
        method=method,
    )

def resolve_fuzzy(
    raw: str,
    registry: CompanyRegistry,
    threshold: float = 0.90,
) -> CompanyMatch | None:

    raw_key = normalise_company_name(raw)
    if not raw_key:
        return None
    best_company = None
    best_score = 0.0
    for registry_key, company_name in registry.normalized.items():
        score = SequenceMatcher(
            None,
            raw_key,
            registry_key,
        ).ratio()

        if score > best_score:
            best_score = score
            best_company = company_name

    if best_score >= threshold:
        return CompanyMatch(
            company_name=best_company,
            method="fuzzy",
        )

    return None


def resolve_company(
    raw: str,
    registry: CompanyRegistry,
) -> CompanyMatch:

    # exact -> normalised -> alias -> fuzzy -> no_match
    if raw is None or not str(raw).strip():
        return CompanyMatch(
            company_name=None,
            method="no_match",
        )

    # Tier 1: exact
    result = resolve_exact(raw, registry)
    if result is not None:
        return result

    # Tier 1: normalised
    result = resolve_normalised(raw, registry)
    if result is not None:
        return result

    # Tier 2: alias
    result = resolve_alias(raw, registry)
    if result is not None:
        return result

    # Tier 3: fuzzy
    result = resolve_fuzzy(raw, registry)
    if result is not None:
        return result

    # Nothing matched
    return CompanyMatch(
        company_name=None,
        method="no_match",
    )