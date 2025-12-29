import csv
import sys
from pathlib import Path


def parse_goodreads_csv(filepath: str | Path) -> set[str]:
    authors = set()

    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if row.get("Exclusive Shelf") != "read":
                continue

            primary_author = row.get("Author", "").strip()
            if primary_author:
                authors.add(primary_author)

            additional = row.get("Additional Authors", "").strip()
            if additional:
                for author in additional.split(","):
                    author = author.strip()
                    if author:
                        authors.add(author)

    return authors


# expected format: - Book Title - Author1, Author2, Author3
def parse_markdown_list(filepath: str | Path) -> set[str]:
    authors = set()

    with open(filepath, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("- "):
                continue

            line = line[2:]
            parts = line.rsplit(" - ", 1)
            if len(parts) != 2:
                continue

            _, author_part = parts
            for author in author_part.split(","):
                author = author.strip()
                if author:
                    authors.add(author)

    return authors


def parse_stdin() -> set[str]:
    authors = set()
    for line in sys.stdin:
        for author in line.split(","):
            name = author.strip()
            if name:
                authors.add(name)
    return authors
