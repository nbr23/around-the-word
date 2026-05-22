# around-the-word

Visualize author birthplaces from your "books read" list as an interactive world heatmap.

## Install

```bash
uv pip install around-the-word
```

## Goodreads input options

Two ways to pull books from Goodreads:

**CSV export** (full data, includes additional authors):

1. Go to [goodreads.com/review/import](https://www.goodreads.com/review/import)
2. Click "Export Library"
3. Wait for the export to complete, then download the CSV file

**Live RSS feed** (no export step, always current; primary author only):

Pass your Goodreads user identifier with `--goodreads-user`. You can find it in the URL of your profile page (e.g. `https://www.goodreads.com/user/show/12345678-username` → `12345678-username`). The feed is paginated and fetched in full automatically.

## Usage

```bash
# From Goodreads CSV export
uvx around-the-word -i goodreads_library_export.csv -f goodreads -o map.html

# From Goodreads live RSS feed (no export needed)
uvx around-the-word -f goodreads-rss --goodreads-user 12345678-username -o map.html

# From a different shelf (default is "read")
uvx around-the-word -f goodreads-rss --goodreads-user 12345678-username --goodreads-shelf to-read -o map.html

# From markdown list (- Title - Author format)
uvx around-the-word -i books.md -f markdown -o map.html

# With caching (recommended for large lists)
uvx around-the-word -i export.csv -f goodreads -c cache.json -o map.html

# Regenerate map from cache only (no API calls)
uvx around-the-word --cache-only -c cache.json -o map.html

# With legend and top 10 countries
uvx around-the-word --cache-only -c cache.json --top 10 -o map.html

# Include all Wikidata citizenships (dual nationals appear in every country)
uvx around-the-word -i export.csv -f goodreads --multi-nationality -c cache.json -o map.html

# From stdin (one author per line, or comma-separated)
echo "Stephen King" | uvx around-the-word -c cache.json -o map.html
cat authors.txt | uvx around-the-word -c cache.json -o map.html
echo "Stephen King, Albert Camus, Terry Pratchett" | uvx around-the-word -c cache.json
# With multiple nationalities
echo "Stephen King, Albert Camus, Terry Pratchett" | uvx around-the-word --multi-nationality -c cache.json
```

## Options

| Flag | Description |
|------|-------------|
| `-v, --version` | Show version and exit |
| `-i, --input` | Input file path (or pipe author names to stdin) |
| `-f, --format` | Input format: `goodreads`, `markdown`, or `goodreads-rss` |
| `--goodreads-user` | Goodreads user identifier (required with `-f goodreads-rss`) |
| `--goodreads-shelf` | Shelf to fetch with `-f goodreads-rss` (default: `read`) |
| `-o, --output` | Output HTML file (default: `author_map.html`) |
| `-d, --delay` | Delay between API requests in seconds (default: 0.5) |
| `-c, --cache` | JSON cache file for author birthplaces |
| `--cache-only` | Regenerate map from cache without lookups |
| `--map-title` | Title displayed on the map (default: "Authors by Birthplace") |
| `--title` | HTML document title (default: "Around the Word") |
| `--colorscale` | Color scale for the map (default: "reds") |
| `--legend` | Show legend with color scale |
| `--top N` | Show top N countries in legend (implies `--legend`) |
| `--include-authors` | Include author names in map hover tooltips |
| `--default-view` | Default toggle view on map load: `authors` or `books` (default: `authors`) |
| `--multi-nationality` | Include every Wikidata citizenship plus birth country (default: birth country only) |

When an input file is provided, the map includes a toggle to switch between counting unique authors or total books per country.

## Cache format

The cache file (`-c/--cache`) maps each author to a list of country names (or `null` when no nationality could be resolved):

```json
{
  "Albert Camus": ["Algeria", "France"],
  "Adrian Tchaikovsky": ["United Kingdom"],
  "Unknown Author": null
}
```
