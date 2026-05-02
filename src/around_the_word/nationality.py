import json
import re
import time
from pathlib import Path
from typing import Optional

import requests

from .constants import NATIONALITY_TO_COUNTRY


def get_nationalities_wikidata(author_name: str, multi: bool = False) -> list[str]:
    if multi:
        sparql_query = """
        SELECT ?birthCountryLabel ?nationalityLabel WHERE {
          ?person wdt:P31 wd:Q5 .
          ?person rdfs:label "%s"@en .
          ?person wdt:P106 ?occupation .
          ?occupation wdt:P279* wd:Q36180 .
          OPTIONAL { ?person wdt:P19/wdt:P17 ?birthCountry . }
          OPTIONAL { ?person wdt:P27 ?nationality . }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        }
        """ % author_name.replace('"', '\\"')
    else:
        sparql_query = """
        SELECT ?birthCountryLabel ?nationalityLabel WHERE {
          ?person wdt:P31 wd:Q5 .
          ?person rdfs:label "%s"@en .
          ?person wdt:P106 ?occupation .
          ?occupation wdt:P279* wd:Q36180 .
          OPTIONAL { ?person wdt:P19/wdt:P17 ?birthCountry . }
          OPTIONAL { ?person wdt:P27 ?nationality . }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        }
        LIMIT 1
        """ % author_name.replace('"', '\\"')

    url = "https://query.wikidata.org/sparql"
    headers = {
        "Accept": "application/json",
        "User-Agent": "AroundTheWord/1.0 (Author nationality visualizer)",
    }

    try:
        response = requests.get(
            url, params={"query": sparql_query}, headers=headers, timeout=10
        )
        response.raise_for_status()
        data = response.json()

        results = data.get("results", {}).get("bindings", [])
        if not results:
            return []

        if not multi:
            if "birthCountryLabel" in results[0]:
                return [results[0]["birthCountryLabel"]["value"]]
            if "nationalityLabel" in results[0]:
                return [results[0]["nationalityLabel"]["value"]]
            return []

        found: list[str] = []
        for row in results:
            for key in ("birthCountryLabel", "nationalityLabel"):
                if key in row:
                    value = row[key]["value"]
                    if value not in found:
                        found.append(value)
        return found
    except Exception as e:
        print(f"  Wikidata error for '{author_name}': {e}")

    return []

WRITER_PROFESSIONS = [
    "writer",
    "author",
    "novelist",
    "poet",
    "playwright",
    "essayist",
    "comics artist",
    "comics creator"
]

# Regex pattern fragment for matching professions
_PROF_PATTERN = "(?:" + "|".join(p.replace(" ", r"\s+") for p in WRITER_PROFESSIONS) + ")"


# Wikipedia parsing fallback
def get_nationality_wikipedia(author_name: str) -> Optional[str]:
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + requests.utils.quote(
        author_name
    )
    headers = {"User-Agent": "AroundTheWord/1.0 (Author nationality visualizer)"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()

        extract = data.get("extract", "")

        # Common patterns
        nationality_pat = r"([A-Z][a-z]+(?:-[A-Z][a-z]+)?)"
        patterns = [
            rf"(?:is|was) an? {nationality_pat}\s+{_PROF_PATTERN}",
            rf"(?:is|was) an? {nationality_pat}\s+(?:and\s+)?(?:\w+\s+)?{_PROF_PATTERN}",
            rf"(?:is|was) the {nationality_pat}\s+{_PROF_PATTERN}",
            rf"\(.*?(\w+)\s+{_PROF_PATTERN}",
        ]

        # Fallback: nationality appears after "is/was a/an" and sentence contains author-related word
        if re.search(rf"\b{_PROF_PATTERN}\b", extract, re.IGNORECASE):
            patterns.append(rf"(?:is|was) an? {nationality_pat}\s+\w+")
            patterns.append(rf"(?:is|was) the? {nationality_pat}\s+\w+")

        for pattern in patterns:
            match = re.search(pattern, extract)
            if match:
                nationality = match.group(1)
                if nationality_to_country(nationality):
                    return nationality

    except Exception as e:
        print(f"  Wikipedia error for '{author_name}': {e}")

    return None


def lookup_author_nationality(author_name: str, multi: bool = False) -> list[str]:
    nationalities = get_nationalities_wikidata(author_name, multi=multi)
    if nationalities:
        return nationalities
    fallback = get_nationality_wikipedia(author_name)
    return [fallback] if fallback else []


def nationality_to_country(nationality: str) -> Optional[str]:
    if nationality in NATIONALITY_TO_COUNTRY:
        return NATIONALITY_TO_COUNTRY[nationality]

    for key, country in NATIONALITY_TO_COUNTRY.items():
        if key.lower() == nationality.lower():
            return country

    countries = set(NATIONALITY_TO_COUNTRY.values())
    if nationality in countries:
        return nationality

    return None


def _normalize(value) -> Optional[list[str]]:
    if value is None:
        return None
    if isinstance(value, str):
        return [value]
    return list(value)


def load_cache(path: Path) -> dict[str, Optional[list[str]]]:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return {k: _normalize(v) for k, v in raw.items()}


def save_cache(path: Path, data: dict[str, Optional[list[str]]]) -> None:
    existing = load_cache(path)
    existing.update(data)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)


def lookup_authors(
    authors: set[str],
    delay: float = 0.5,
    cache_path: Optional[Path] = None,
    multi: bool = False,
) -> dict[str, Optional[list[str]]]:
    cache = load_cache(cache_path) if cache_path else {}
    results: dict[str, Optional[list[str]]] = {}
    author_list = sorted(authors)
    fetched_count = 0

    for i, author in enumerate(author_list):
        if cache.get(author):
            results[author] = cache[author]
            label = ", ".join(cache[author]) if cache[author] else "NOT FOUND"
            print(f"[{i + 1}/{len(author_list)}] {author}: {label} (cached)")
            continue

        if fetched_count > 0:
            time.sleep(delay)

        print(f"[{i + 1}/{len(author_list)}] Looking up: {author}")
        nationalities = lookup_author_nationality(author, multi=multi)

        countries: list[str] = []
        for nationality in nationalities:
            country = nationality_to_country(nationality)
            if country and country not in countries:
                countries.append(country)

        if countries:
            results[author] = countries
            print(f"  -> {', '.join(nationalities)} -> {', '.join(countries)}")
        elif nationalities:
            results[author] = None
            print(f"  -> {', '.join(nationalities)} -> UNMAPPED")
        else:
            results[author] = None
            print("  -> NOT FOUND")

        cache[author] = results[author]
        fetched_count += 1

    if cache_path:
        save_cache(cache_path, {k: cache[k] for k in cache if k in authors})

    return results
