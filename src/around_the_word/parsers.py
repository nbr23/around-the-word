import csv
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

import requests


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


def parse_goodreads_rss(user: str, shelf: str = "read") -> list[tuple[str, str]]:
    book_author_pairs = []
    max_pages = 50
    base_url = f"https://www.goodreads.com/review/list_rss/{user}"

    for page in range(1, max_pages + 1):
        resp = requests.get(
            base_url,
            params={"shelf": shelf, "page": page},
            headers={"User-Agent": "around-the-word"},
            timeout=30,
        )
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        items = root.findall(".//item")
        print(f"Fetched page {page} ({len(items)} items)")

        if not items:
            break

        for item in items:
            author_el = item.find("author_name")
            title_el = item.find("title")
            author = (author_el.text or "").strip() if author_el is not None else ""
            title = (title_el.text or "").strip() if title_el is not None else ""
            if author:
                book_author_pairs.append((author, title))
    else:
        print(f"Warning: hit max_pages={max_pages} cap; results may be truncated", file=sys.stderr)

    return book_author_pairs


def parse_stdin() -> list[tuple[str, str]]:
    book_author_pairs = []
    for line in sys.stdin:
        for author in line.split(","):
            name = author.strip()
            if name:
                book_author_pairs.append((name, ""))
    return book_author_pairs
