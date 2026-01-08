# around-the-word

Visualize author birthplaces from your "books read" list as an interactive world heatmap.

## Install

```bash
uv pip install around-the-word
```

## Exporting from Goodreads

1. Go to [goodreads.com/review/import](https://www.goodreads.com/review/import)
2. Click "Export Library"
3. Wait for the export to complete, then download the CSV file

## Usage

```bash
# From Goodreads CSV export
uvx around-the-word -i goodreads_library_export.csv -f goodreads -o map.html

# From markdown list (- Title - Author format)
uvx around-the-word -i books.md -f markdown -o map.html

# With caching (recommended for large lists)
uvx around-the-word -i export.csv -f goodreads -c cache.json -o map.html

# Regenerate map from cache only (no API calls)
uvx around-the-word --cache-only -c cache.json -o map.html

# With legend and top 10 countries
uvx around-the-word --cache-only -c cache.json --top 10 -o map.html

# From stdin (one author per line, or comma-separated)
echo "Stephen King" | uvx around-the-word -c cache.json -o map.html
cat authors.txt | uvx around-the-word -c cache.json -o map.html
echo "King, Rowling, Pratchett" | uvx around-the-word -c cache.json
```

## Options

| Flag | Description |
|------|-------------|
| `-v, --version` | Show version and exit |
| `-i, --input` | Input file path (or pipe author names to stdin) |
| `-f, --format` | Input format: `goodreads` or `markdown` |
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

When an input file is provided, the map includes a toggle to switch between counting unique authors or total books per country.
