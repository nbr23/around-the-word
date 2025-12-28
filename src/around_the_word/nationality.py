import json
import re
import time
from pathlib import Path
from typing import Optional

import requests

from .constants import NATIONALITY_TO_COUNTRY


def get_nationality_wikidata(author_name: str) -> Optional[str]:
    sparql_query = """
    SELECT ?personLabel ?birthCountryLabel ?nationalityLabel WHERE {
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
        if results:
            # Prefer birth country over citizenship
            if "birthCountryLabel" in results[0]:
                return results[0]["birthCountryLabel"]["value"]
            if "nationalityLabel" in results[0]:
                return results[0]["nationalityLabel"]["value"]
    except Exception as e:
        print(f"  Wikidata error for '{author_name}': {e}")

    return None

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


def lookup_author_nationality(author_name: str) -> Optional[str]:
    nationality = get_nationality_wikidata(author_name)
    if nationality:
        return nationality
    return get_nationality_wikipedia(author_name)


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


def load_cache(path: Path) -> dict[str, Optional[str]]:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_cache(path: Path, data: dict[str, Optional[str]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def lookup_authors(
    authors: set[str], delay: float = 0.5, cache_path: Optional[Path] = None
) -> dict[str, Optional[str]]:
    cache = load_cache(cache_path) if cache_path else {}
    results = {}
    author_list = sorted(authors)
    fetched_count = 0

    for i, author in enumerate(author_list):
        if cache.get(author):
            results[author] = cache[author]
            print(f"[{i + 1}/{len(author_list)}] {author}: {cache[author] or 'NOT FOUND'} (cached)")
            continue

        if fetched_count > 0:
            time.sleep(delay)

        print(f"[{i + 1}/{len(author_list)}] Looking up: {author}")
        nationality = lookup_author_nationality(author)

        if nationality:
            country = nationality_to_country(nationality)
            results[author] = country
            print(f"  -> {nationality} -> {country or 'UNMAPPED'}")
        else:
            results[author] = None
            print("  -> NOT FOUND")

        cache[author] = results[author]
        fetched_count += 1

    if cache_path:
        save_cache(cache_path, cache)

    return results
