import argparse
import sys
from importlib.metadata import version
from pathlib import Path

from .map_generator import generate_map
from .parsers import (
    parse_goodreads_csv,
    parse_goodreads_rss,
    parse_markdown_list,
    parse_stdin,
)
from .nationality import lookup_authors, load_cache

__version__ = version("around-the-word")


def _parse_input(args):
    if args.format == "goodreads-rss":
        if not args.goodreads_user:
            print("Error: -f goodreads-rss requires --goodreads-user", file=sys.stderr)
            sys.exit(1)
        if args.input:
            print("Error: -i/--input is not used with -f goodreads-rss (use --goodreads-user)", file=sys.stderr)
            sys.exit(1)
        print(f"Fetching Goodreads RSS for user {args.goodreads_user} (shelf: {args.goodreads_shelf})...")
        return parse_goodreads_rss(args.goodreads_user, args.goodreads_shelf)

    if not args.input:
        print("Error: -i/--input is required for this format", file=sys.stderr)
        sys.exit(1)
    if not args.input.exists():
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    print(f"Parsing {args.input}...")
    if args.format == "goodreads":
        return parse_goodreads_csv(args.input)
    return parse_markdown_list(args.input)


def main():
    parser = argparse.ArgumentParser(
        description="Visualize author nationalities as a world heatmap"
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        help="Input file path (not required with --cache-only)",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["goodreads", "markdown", "goodreads-rss"],
        help="Input format: goodreads (CSV export), markdown (- Title - Authors), or goodreads-rss (live RSS feed; primary author only, no additional authors)",
    )
    parser.add_argument(
        "--goodreads-user",
        help="Goodreads user identifier for -f goodreads-rss (e.g. 12345678-username)",
    )
    parser.add_argument(
        "--goodreads-shelf",
        default="read",
        help="Goodreads shelf to fetch with -f goodreads-rss (default: read)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("author_map.html"),
        help="Output HTML file path (default: author_map.html)",
    )
    parser.add_argument(
        "-d",
        "--delay",
        type=float,
        default=0.5,
        help="Delay between API requests in seconds (default: 0.5)",
    )
    parser.add_argument(
        "-c",
        "--cache",
        type=Path,
        help="JSON file to cache author nationalities (enables manual corrections)",
    )
    parser.add_argument(
        "--cache-only",
        action="store_true",
        help="Skip lookups and regenerate map from cache only",
    )
    parser.add_argument(
        "--map-title",
        default=None,
        help="Title displayed on the map (default: 'Authors by Nationality')",
    )
    parser.add_argument(
        "--title",
        default="Around the Word",
        help="HTML document title (default: 'Around the Word')",
    )
    parser.add_argument(
        "--colorscale",
        default="reds",
        help="Color scale for the map: reds, blues, greens, viridis, etc. (default: 'reds')",
    )
    parser.add_argument(
        "--legend",
        action="store_true",
        help="Show legend with color scale",
    )
    parser.add_argument(
        "--top",
        type=int,
        metavar="N",
        help="Show top N countries in legend (implies --legend)",
    )
    parser.add_argument(
        "--include-authors",
        action="store_true",
        help="Include author names in map hover tooltips",
    )
    parser.add_argument(
        "--default-view",
        choices=["authors", "books"],
        default="authors",
        help="Default toggle view on map load (default: authors)",
    )
    parser.add_argument(
        "--multi-nationality",
        action="store_true",
        help="Include all Wikidata citizenships in addition to birth country (default: single)",
    )

    args = parser.parse_args()

    if args.top:
        args.legend = True

    if args.map_title is None:
        args.map_title = "Authors by Nationality"

    print(f"around-the-word v{__version__}")

    book_author_pairs = []

    if args.cache_only:
        if not args.cache:
            print("Error: --cache-only requires --cache", file=sys.stderr)
            sys.exit(1)
        if not args.cache.exists():
            print(f"Error: Cache file not found: {args.cache}", file=sys.stderr)
            sys.exit(1)
        print(f"Loading cache: {args.cache}")
        author_countries = load_cache(args.cache)
        print(f"Loaded {len(author_countries)} authors from cache")

        if args.input or args.format == "goodreads-rss":
            if not args.format:
                print("Error: -f/--format is required with -i/--input", file=sys.stderr)
                sys.exit(1)
            book_author_pairs = _parse_input(args)
            print(f"Found {len(book_author_pairs)} book-author entries")
    else:
        if args.input or args.format == "goodreads-rss":
            if not args.format:
                print("Error: -f/--format is required with -i/--input", file=sys.stderr)
                sys.exit(1)
            book_author_pairs = _parse_input(args)
        else:
            if sys.stdin.isatty():
                print("Error: No input. Provide -i/--input, -f goodreads-rss, or pipe author names to stdin", file=sys.stderr)
                sys.exit(1)
            print("Reading authors from stdin...")
            book_author_pairs = parse_stdin()

        authors = {author for author, _ in book_author_pairs}
        print(f"Found {len(authors)} unique authors\n")

        if not authors:
            print("No authors found.", file=sys.stderr)
            sys.exit(1)

        print("Looking up author nationalities...")
        author_countries = lookup_authors(
            authors,
            delay=args.delay,
            cache_path=args.cache,
            multi=args.multi_nationality,
        )

    if sum(1 for c in author_countries.values() if c) > 0:
        print(f"\nGenerating map: {args.output}")
        output = generate_map(
            author_countries,
            args.output,
            book_author_pairs=book_author_pairs,
            default_view=args.default_view,
            map_title=args.map_title,
            page_title=args.title,
            colorscale=args.colorscale,
            show_legend=args.legend,
            top_n=args.top,
            include_authors=args.include_authors,
        )
        print(f"Map saved to: {output.absolute()}")
    else:
        print("\nNo nationality data found - skipping map generation.")
        sys.exit(1)


if __name__ == "__main__":
    main()
