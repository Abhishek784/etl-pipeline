
def normalise_category(raw: str) -> str:
    if raw is None:
        return ""

    return " ".join(raw.lower().split())

def build_category_lookup(category_map: dict[str, list[str]] ) -> dict[str, str]:
    lookup = {}
    for canonical, variants in category_map.items():

        for variant in variants:
            key = normalise_category(variant)
            lookup[key] = canonical

    return lookup


def standardise_category(raw: str, category_map: dict[str, list[str]],) -> str:

    lookup = build_category_lookup(category_map)
    key = normalise_category(raw)
    return lookup.get(key, "UNKNOWN")