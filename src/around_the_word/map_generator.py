from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional

import plotly.graph_objects as go


def generate_map(
    author_countries: dict[str, Optional[str]],
    output_path: str | Path = "author_map.html",
    include_authors: bool = False,
    map_title: str = "Authors by Nationality",
    page_title: str = "Around the Word",
) -> Path:
    authors_by_country: dict[str, list[str]] = defaultdict(list)
    for author, country in author_countries.items():
        if country:
            authors_by_country[country].append(author)

    if not authors_by_country:
        raise ValueError("No valid country data to map")

    countries = list(authors_by_country.keys())
    counts = [len(authors_by_country[c]) for c in countries]

    if include_authors:
        hover_texts = []
        for country in countries:
            authors = sorted(authors_by_country[country])
            if len(authors) > 25:
                author_list = "<br>".join(authors[:25]) + f"<br>...and {len(authors) - 25} more"
            else:
                author_list = "<br>".join(authors)
            hover_texts.append(author_list)

        fig = go.Figure(
            data=go.Choropleth(
                locations=countries,
                locationmode="country names",
                z=counts,
                colorscale="Greens",
                showscale=False,
                text=hover_texts,
                hovertemplate="<b>%{location}</b><br>Authors: %{z}<br><br>%{text}<extra></extra>",
            )
        )
    else:
        fig = go.Figure(
            data=go.Choropleth(
                locations=countries,
                locationmode="country names",
                z=counts,
                colorscale="Greens",
                showscale=False,
                hovertemplate="<b>%{location}</b><br>Authors: %{z}<extra></extra>",
            )
        )

    fig.update_layout(
        title_text=map_title,
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type="natural earth",
        ),
        margin=dict(l=0, r=0, t=50, b=0),
    )

    output_path = Path(output_path)
    html_content = fig.to_html(config={"displayModeBar": False})
    html_content = html_content.replace("<head>", f"<head><title>{page_title}</title>", 1)
    output_path.write_text(html_content)

    return output_path
