import argparse
import sys
from pathlib import Path

from .map_generator import generate_map
from .parsers import parse_goodreads_csv, parse_markdown_list
from .nationality import lookup_authors


def main():
    parser = argparse.ArgumentParser(
        description="Visualize author nationalities as a world heatmap"
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        required=True,
        help="Input file path",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["goodreads", "markdown"],
        required=True,
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

    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing {args.input}...")
    if args.format == "goodreads":
        authors = parse_goodreads_csv(args.input)
    else:
        authors = parse_markdown_list(args.input)
    print(f"Found {len(authors)} unique authors\n")

    if not authors:
        print("No authors found.", file=sys.stderr)
        sys.exit(1)

    print("Looking up author nationalities...")
    author_countries = lookup_authors(authors, delay=args.delay)

    if sum(1 for c in author_countries.values() if c) > 0:
        print(f"\nGenerating map: {args.output}")
        output = generate_map(author_countries, args.output)
        print(f"Map saved to: {output.absolute()}")
    else:
        print("\nNo nationality data found - skipping map generation.")
        sys.exit(1)


if __name__ == "__main__":
    main()
