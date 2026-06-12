import pytest

from around_the_word import map_generator
from around_the_word.map_generator import generate_map

FAKE_ASSETS = {
    "d3.v7.min.js": "/* d3 stub */",
    "topojson-client.min.js": "/* topojson stub */",
    "world-110m.json": '{"type": "Topology", "objects": {"countries": {}}}',
}


@pytest.fixture(autouse=True)
def stub_assets(monkeypatch):
    monkeypatch.setattr(map_generator, "_load_asset", lambda name: FAKE_ASSETS[name])


def test_generate_map_writes_output(tmp_path):
    output = tmp_path / "map.html"

    result = generate_map({"Jane Doe": ["France"]}, output)

    assert result == output
    html = output.read_text()
    assert "'France': 1" in html
    assert "/* d3 stub */" in html


def test_generate_map_raises_without_country_data(tmp_path):
    with pytest.raises(ValueError):
        generate_map({"Jane Doe": None}, tmp_path / "map.html")


def test_generate_map_counts_books_per_country(tmp_path):
    output = tmp_path / "map.html"
    pairs = [("Jane Doe", "Book One"), ("Jane Doe", "Book Two"), ("John Smith", "Book Three")]
    authors = {"Jane Doe": ["France"], "John Smith": ["France"]}

    generate_map(authors, output, book_author_pairs=pairs)

    html = output.read_text()
    assert "'France': 3" in html
    assert "const hasBookData = true;" in html


def test_generate_map_counts_unique_authors_per_country(tmp_path):
    output = tmp_path / "map.html"
    pairs = [("Jane Doe", "Book One"), ("Jane Doe", "Book Two")]

    generate_map({"Jane Doe": ["France", "Belgium"]}, output, book_author_pairs=pairs)

    html = output.read_text()
    assert "const authorCounts = {'France': 1, 'Belgium': 1};" in html


def test_generate_map_include_authors(tmp_path):
    output = tmp_path / "map.html"

    generate_map({"Jane Doe": ["France"]}, output, include_authors=True)

    assert '"Jane Doe"' in output.read_text()


def test_generate_map_excludes_authors_by_default(tmp_path):
    output = tmp_path / "map.html"

    generate_map({"Jane Doe": ["France"]}, output)

    html = output.read_text()
    assert "Jane Doe" not in html
    assert "const authorsByCountry = {};" in html


def test_generate_map_titles_and_default_view(tmp_path):
    output = tmp_path / "map.html"

    generate_map(
        {"Jane Doe": ["France"]},
        output,
        book_author_pairs=[("Jane Doe", "Book One")],
        default_view="books",
        map_title="My Map",
        page_title="My Page",
    )

    html = output.read_text()
    assert "<title>My Page</title>" in html
    assert "<h1>My Map</h1>" in html
    assert 'let currentMode = "books";' in html


def test_generate_map_unknown_colorscale_falls_back_to_reds(tmp_path):
    output = tmp_path / "map.html"

    generate_map({"Jane Doe": ["France"]}, output, colorscale="nonexistent")

    assert '"interpolateReds"' in output.read_text()
