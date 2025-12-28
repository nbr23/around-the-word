from collections import Counter
from pathlib import Path
from typing import Optional

import plotly.graph_objects as go


def generate_map(
    author_countries: dict[str, Optional[str]],
    output_path: str | Path = "author_map.html",
) -> Path:
    # Count unique authors per country
    country_counts = Counter(
        country for country in author_countries.values() if country
    )

    if not country_counts:
        raise ValueError("No valid country data to map")

    countries = list(country_counts.keys())
    counts = list(country_counts.values())

    fig = go.Figure(
        data=go.Choropleth(
            locations=countries,
            locationmode="country names",
            z=counts,
            colorscale="Viridis",
            colorbar_title="Authors",
        )
    )

    fig.update_layout(
        title_text="Authors by Nationality",
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type="natural earth",
        ),
        margin=dict(l=0, r=0, t=50, b=0),
    )

    output_path = Path(output_path)
    fig.write_html(output_path)

    return output_path
