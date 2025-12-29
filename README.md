# around-the-word

Visualize author nationalities from your "books read" list as an interactive world heatmap.

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
```

## Options

| Flag | Description |
|------|-------------|
| `-v, --version` | Show version and exit |
| `-i, --input` | Input file path |
| `-f, --format` | Input format: `goodreads` or `markdown` |
| `-o, --output` | Output HTML file (default: `author_map.html`) |
| `-d, --delay` | Delay between API requests in seconds (default: 0.5) |
| `-c, --cache` | JSON cache file for author nationalities |
| `--cache-only` | Regenerate map from cache without lookups |
| `--include-authors` | Include author names in map hover tooltips |
