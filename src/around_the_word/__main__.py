import argparse
import sys
from importlib.metadata import version
from pathlib import Path

from .map_generator import generate_map
from .parsers import parse_goodreads_csv, parse_markdown_list, parse_stdin
from .nationality import lookup_authors, load_cache

__version__ = version("around-the-word")


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
        choices=["goodreads", "markdown"],
        help="Input format: goodreads (CSV export) or markdown (- Title - Authors)",
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

        if args.input:
            if not args.format:
                print("Error: -f/--format is required with -i/--input", file=sys.stderr)
                sys.exit(1)
            if not args.input.exists():
                print(f"Error: File not found: {args.input}", file=sys.stderr)
                sys.exit(1)
            print(f"Parsing {args.input} for book counts...")
            if args.format == "goodreads":
                book_author_pairs = parse_goodreads_csv(args.input)
            else:
                book_author_pairs = parse_markdown_list(args.input)
            print(f"Found {len(book_author_pairs)} book-author entries")
    else:
        if args.input:
            if not args.format:
                print("Error: -f/--format is required with -i/--input", file=sys.stderr)
                sys.exit(1)
            if not args.input.exists():
                print(f"Error: File not found: {args.input}", file=sys.stderr)
                sys.exit(1)
            print(f"Parsing {args.input}...")
            if args.format == "goodreads":
                book_author_pairs = parse_goodreads_csv(args.input)
            else:
                book_author_pairs = parse_markdown_list(args.input)
        else:
            if sys.stdin.isatty():
                print("Error: No input. Provide -i/--input or pipe author names to stdin", file=sys.stderr)
                sys.exit(1)
            print("Reading authors from stdin...")
            book_author_pairs = parse_stdin()

        authors = {author for author, _ in book_author_pairs}
        print(f"Found {len(authors)} unique authors\n")

        if not authors:
            print("No authors found.", file=sys.stderr)
            sys.exit(1)

        print("Looking up author nationalities...")
        author_countries = lookup_authors(authors, delay=args.delay, cache_path=args.cache)

    if sum(1 for c in author_countries.values() if c) > 0:
        print(f"\nGenerating map: {args.output}")
        output = generate_map(
            author_countries,
            args.output,
            book_author_pairs=book_author_pairs,
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
