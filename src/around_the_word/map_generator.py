from collections import defaultdict
from pathlib import Path

from jinja2 import Environment, PackageLoader

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


def _load_asset(name: str) -> str:
    if name not in _assets_cache:
        assets_dir = Path(__file__).parent / "assets"
        _assets_cache[name] = (assets_dir / name).read_text()
    return _assets_cache[name]


def generate_map(
    author_countries: dict[str, str | None],
    output_path: str | Path = "author_map.html",
    map_title: str = "Authors by Nationality",
    page_title: str = "Around the Word",
    colorscale: str = "reds",
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
    )

    output_path = Path(output_path)
    output_path.write_text(html_content)

    return output_path
