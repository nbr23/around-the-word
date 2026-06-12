import json

from around_the_word import nationality
from around_the_word.nationality import (
    get_nationalities_wikidata,
    get_nationality_wikipedia,
    load_cache,
    lookup_authors,
    nationality_to_country,
    save_cache,
)


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


def test_nationality_to_country_known():
    assert nationality_to_country("American") == "United States"
    assert nationality_to_country("British") == "United Kingdom"


def test_nationality_to_country_case_insensitive():
    assert nationality_to_country("american") == "United States"


def test_nationality_to_country_accepts_country_name():
    assert nationality_to_country("France") == "France"


def test_nationality_to_country_unknown():
    assert nationality_to_country("Klingon") is None


def test_load_cache_missing_file(tmp_path):
    assert load_cache(tmp_path / "missing.json") == {}


def test_load_cache_normalizes_values(tmp_path):
    cache_file = tmp_path / "cache.json"
    cache_file.write_text(
        json.dumps({"Old Format": "France", "New Format": ["France", "Belgium"], "Not Found": None})
    )

    cache = load_cache(cache_file)

    assert cache == {
        "Old Format": ["France"],
        "New Format": ["France", "Belgium"],
        "Not Found": None,
    }


def test_save_cache_merges_with_existing(tmp_path):
    cache_file = tmp_path / "cache.json"
    cache_file.write_text(json.dumps({"Jane Doe": ["France"]}))

    save_cache(cache_file, {"John Smith": ["United Kingdom"]})

    assert load_cache(cache_file) == {
        "Jane Doe": ["France"],
        "John Smith": ["United Kingdom"],
    }


def test_lookup_authors_uses_cache(tmp_path, monkeypatch):
    cache_file = tmp_path / "cache.json"
    cache_file.write_text(json.dumps({"Jane Doe": ["France"]}))
    looked_up = []

    def fake_lookup(author, multi=False):
        looked_up.append(author)
        return ["British"]

    monkeypatch.setattr(nationality, "lookup_author_nationality", fake_lookup)

    results = lookup_authors({"Jane Doe", "John Smith"}, delay=0, cache_path=cache_file)

    assert looked_up == ["John Smith"]
    assert results == {"Jane Doe": ["France"], "John Smith": ["United Kingdom"]}
    assert load_cache(cache_file)["John Smith"] == ["United Kingdom"]


def test_lookup_authors_retries_null_cache_entries(tmp_path, monkeypatch):
    cache_file = tmp_path / "cache.json"
    cache_file.write_text(json.dumps({"Jane Doe": None}))

    monkeypatch.setattr(
        nationality, "lookup_author_nationality", lambda author, multi=False: ["French"]
    )

    results = lookup_authors({"Jane Doe"}, delay=0, cache_path=cache_file)

    assert results == {"Jane Doe": ["France"]}


def test_lookup_authors_records_not_found(tmp_path, monkeypatch):
    cache_file = tmp_path / "cache.json"
    monkeypatch.setattr(
        nationality, "lookup_author_nationality", lambda author, multi=False: []
    )

    results = lookup_authors({"Jane Doe"}, delay=0, cache_path=cache_file)

    assert results == {"Jane Doe": None}
    cache = json.loads(cache_file.read_text())
    assert cache == {"Jane Doe": None}


def test_get_nationalities_wikidata_single_prefers_birth_country(monkeypatch):
    payload = {
        "results": {
            "bindings": [
                {
                    "birthCountryLabel": {"value": "France"},
                    "nationalityLabel": {"value": "Belgium"},
                }
            ]
        }
    }
    monkeypatch.setattr(
        nationality.requests,
        "get",
        lambda url, params=None, headers=None, timeout=None: FakeResponse(payload),
    )

    assert get_nationalities_wikidata("Jane Doe") == ["France"]


def test_get_nationalities_wikidata_multi_deduplicates(monkeypatch):
    payload = {
        "results": {
            "bindings": [
                {
                    "birthCountryLabel": {"value": "France"},
                    "nationalityLabel": {"value": "Belgium"},
                },
                {
                    "birthCountryLabel": {"value": "France"},
                    "nationalityLabel": {"value": "France"},
                },
            ]
        }
    }
    monkeypatch.setattr(
        nationality.requests,
        "get",
        lambda url, params=None, headers=None, timeout=None: FakeResponse(payload),
    )

    assert get_nationalities_wikidata("Jane Doe", multi=True) == ["France", "Belgium"]


def test_get_nationalities_wikidata_no_results(monkeypatch):
    monkeypatch.setattr(
        nationality.requests,
        "get",
        lambda url, params=None, headers=None, timeout=None: FakeResponse(
            {"results": {"bindings": []}}
        ),
    )

    assert get_nationalities_wikidata("Jane Doe") == []


def test_get_nationality_wikipedia_extracts_nationality(monkeypatch):
    payload = {"extract": "Jane Doe (born 1970) is an American writer of fiction."}
    monkeypatch.setattr(
        nationality.requests,
        "get",
        lambda url, headers=None, timeout=None: FakeResponse(payload),
    )

    assert get_nationality_wikipedia("Jane Doe") == "American"


def test_get_nationality_wikipedia_handles_404(monkeypatch):
    monkeypatch.setattr(
        nationality.requests,
        "get",
        lambda url, headers=None, timeout=None: FakeResponse({}, status_code=404),
    )

    assert get_nationality_wikipedia("Jane Doe") is None


def test_get_nationality_wikipedia_ignores_unmappable_adjective(monkeypatch):
    payload = {"extract": "Jane Doe is a Prolific writer."}
    monkeypatch.setattr(
        nationality.requests,
        "get",
        lambda url, headers=None, timeout=None: FakeResponse(payload),
    )

    assert get_nationality_wikipedia("Jane Doe") is None
