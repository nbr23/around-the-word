import urllib.request
from collections import defaultdict
from pathlib import Path

from jinja2 import Environment, PackageLoader

ASSET_URLS = {
    "d3.v7.min.js": "https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js",
    "topojson-client.min.js": "https://cdn.jsdelivr.net/npm/topojson-client@3/dist/topojson-client.min.js",
    "world-110m.json": "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json",
}

# D3 color scale names mapping
COLOR_SCALES = {
    "reds": "interpolateReds",
    "blues": "interpolateBlues",
    "greens": "interpolateGreens",
    "oranges": "interpolateOranges",
    "purples": "interpolatePurples",
    "greys": "interpolateGreys",
    "ylgnbu": "interpolateYlGnBu",
    "ylorbr": "interpolateYlOrBr",
    "rdylgn": "interpolateRdYlGn",
    "spectral": "interpolateSpectral",
    "viridis": "interpolateViridis",
    "plasma": "interpolatePlasma",
    "inferno": "interpolateInferno",
    "magma": "interpolateMagma",
    "turbo": "interpolateTurbo",
}

_assets_cache: dict[str, str] = {}


def _get_cache_dir() -> Path | None:
    cache_dir = Path.home() / ".cache" / "around-the-word"
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir
    except OSError:
        pass
    tmp_dir = Path("/tmp/around-the-word")
    try:
        tmp_dir.mkdir(parents=True, exist_ok=True)
        return tmp_dir
    except OSError:
        return None


def _load_asset(name: str) -> str:
    if name in _assets_cache:
        return _assets_cache[name]

    cache_dir = _get_cache_dir()
    if cache_dir:
        cached_file = cache_dir / name
        if cached_file.exists():
            _assets_cache[name] = cached_file.read_text()
            return _assets_cache[name]

    url = ASSET_URLS.get(name)
    if not url:
        raise ValueError(f"Unknown asset: {name}")

    with urllib.request.urlopen(url) as response:
        content = response.read().decode("utf-8")

    _assets_cache[name] = content
    if cache_dir:
        (cache_dir / name).write_text(content)

    return content


def generate_map(
    author_countries: dict[str, str | None],
    output_path: str | Path = "author_map.html",
    map_title: str = "Authors by Nationality",
    page_title: str = "Around the Word",
    colorscale: str = "reds",
    show_legend: bool = False,
    top_n: int | None = None,
    include_authors: bool = False,
) -> Path:
    authors_by_country: dict[str, list[str]] = defaultdict(list)
    for author, country in author_countries.items():
        if country:
            authors_by_country[country].append(author)

    if not authors_by_country:
        raise ValueError("No valid country data to map")

    author_counts = {country: len(authors) for country, authors in authors_by_country.items()}

    d3_color_scale = COLOR_SCALES.get(colorscale.lower(), "interpolateReds")

    env = Environment(loader=PackageLoader("around_the_word", "templates"))
    template = env.get_template("map.html.j2")

    html_content = template.render(
        page_title=page_title,
        map_title=map_title,
        d3_js=_load_asset("d3.v7.min.js"),
        topojson_js=_load_asset("topojson-client.min.js"),
        topojson_data=_load_asset("world-110m.json"),
        author_counts=author_counts,
        color_scale=f'"{d3_color_scale}"',
        show_legend=show_legend,
        top_n=top_n or 0,
        authors_by_country=dict(authors_by_country) if include_authors else {},
    )

    output_path = Path(output_path)
    output_path.write_text(html_content)

    return output_path
