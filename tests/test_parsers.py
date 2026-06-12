import io
import sys

from around_the_word import parsers
from around_the_word.parsers import (
    parse_goodreads_csv,
    parse_goodreads_rss,
    parse_markdown_list,
    parse_stdin,
)


def test_parse_goodreads_csv(tmp_path):
    csv_file = tmp_path / "goodreads.csv"
    csv_file.write_text(
        "Title,Author,Additional Authors,Exclusive Shelf\n"
        "Solo Book,Jane Doe,,read\n"
        "Duo Book,Jane Doe,\"John Smith, Ann Lee\",read\n"
        "Unread Book,Bob Gray,,to-read\n"
        "No Author,,,read\n",
        encoding="utf-8",
    )

    pairs = parse_goodreads_csv(csv_file)

    assert pairs == [
        ("Jane Doe", "Solo Book"),
        ("Jane Doe", "Duo Book"),
        ("John Smith", "Duo Book"),
        ("Ann Lee", "Duo Book"),
    ]


def test_parse_markdown_list(tmp_path):
    md_file = tmp_path / "books.md"
    md_file.write_text(
        "# My books\n"
        "- Solo Book - Jane Doe\n"
        "- Duo Book - Jane Doe, John Smith\n"
        "- Title - With - Dashes - Ann Lee\n"
        "- No author separator\n"
        "not a list item - Bob Gray\n",
        encoding="utf-8",
    )

    pairs = parse_markdown_list(md_file)

    assert pairs == [
        ("Jane Doe", "Solo Book"),
        ("Jane Doe", "Duo Book"),
        ("John Smith", "Duo Book"),
        ("Ann Lee", "Title - With - Dashes"),
    ]


def test_parse_stdin(monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.StringIO("Jane Doe, John Smith\nAnn Lee\n\n"))

    pairs = parse_stdin()

    assert pairs == [
        ("Jane Doe", ""),
        ("John Smith", ""),
        ("Ann Lee", ""),
    ]


class FakeResponse:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass


def rss_page(items):
    items_xml = "".join(
        f"<item><title>{title}</title><author_name>{author}</author_name></item>"
        for title, author in items
    )
    return FakeResponse(f"<rss><channel>{items_xml}</channel></rss>".encode())


def test_parse_goodreads_rss_paginates_until_empty(monkeypatch):
    pages = {
        1: rss_page([("Book One", "Jane Doe"), ("Book Two", "John Smith")]),
        2: rss_page([("Book Three", "Ann Lee")]),
        3: rss_page([]),
    }
    requested = []

    def fake_get(url, params=None, headers=None, timeout=None):
        requested.append(params["page"])
        return pages[params["page"]]

    monkeypatch.setattr(parsers.requests, "get", fake_get)

    pairs = parse_goodreads_rss("12345-user", shelf="read")

    assert requested == [1, 2, 3]
    assert pairs == [
        ("Jane Doe", "Book One"),
        ("John Smith", "Book Two"),
        ("Ann Lee", "Book Three"),
    ]


def test_parse_goodreads_rss_skips_items_without_author(monkeypatch):
    pages = {
        1: FakeResponse(
            b"<rss><channel>"
            b"<item><title>Orphan Book</title></item>"
            b"<item><title>Good Book</title><author_name>Jane Doe</author_name></item>"
            b"</channel></rss>"
        ),
        2: rss_page([]),
    }

    monkeypatch.setattr(
        parsers.requests,
        "get",
        lambda url, params=None, headers=None, timeout=None: pages[params["page"]],
    )

    pairs = parse_goodreads_rss("12345-user")

    assert pairs == [("Jane Doe", "Good Book")]
