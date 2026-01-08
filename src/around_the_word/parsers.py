import csv
import sys
from pathlib import Path


def parse_goodreads_csv(filepath: str | Path) -> list[tuple[str, str]]:
    book_author_pairs = []

    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if row.get("Exclusive Shelf") != "read":
                continue

            title = row.get("Title", "").strip()

            primary_author = row.get("Author", "").strip()
            if primary_author:
                book_author_pairs.append((primary_author, title))

            additional = row.get("Additional Authors", "").strip()
            if additional:
                for author in additional.split(","):
                    author = author.strip()
                    if author:
                        book_author_pairs.append((author, title))

    return book_author_pairs


# expected format: - Book Title - Author1, Author2, Author3
def parse_markdown_list(filepath: str | Path) -> list[tuple[str, str]]:
    book_author_pairs = []

    with open(filepath, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("- "):
                continue

            line = line[2:]
            parts = line.rsplit(" - ", 1)
            if len(parts) != 2:
                continue

            title, author_part = parts
            for author in author_part.split(","):
                author = author.strip()
                if author:
                    book_author_pairs.append((author, title))

    return book_author_pairs


def parse_stdin() -> list[tuple[str, str]]:
    book_author_pairs = []
    for line in sys.stdin:
        for author in line.split(","):
            name = author.strip()
            if name:
                book_author_pairs.append((name, ""))
    return book_author_pairs
