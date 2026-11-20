"""Turn untrusted HTML into inert data. Nothing here executes or fetches anything."""
from __future__ import annotations

from html.parser import HTMLParser

_SKIP_TAGS = {"script", "style", "head", "title"}


class _Extractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.text_parts: list[str] = []
        self.links: list[tuple[str, str]] = []  # (href, anchor text)
        self._skip_depth = 0
        self._current_href: str | None = None
        self._current_anchor: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
        elif tag == "a":
            href = dict(attrs).get("href")
            if href:
                self._current_href = href.strip()
                self._current_anchor = []
        elif tag in {"br", "p", "div", "tr", "li"}:
            self.text_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
        elif tag == "a" and self._current_href is not None:
            anchor = "".join(self._current_anchor).strip()
            self.links.append((self._current_href, anchor))
            self._current_href = None
            self._current_anchor = []

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        self.text_parts.append(data)
        if self._current_href is not None:
            self._current_anchor.append(data)


def _run(html: str) -> _Extractor:
    parser = _Extractor()
    try:
        parser.feed(html)
        parser.close()
    except Exception:  # malformed HTML must never crash analysis
        pass
    return parser


def html_to_text(html: str) -> str:
    return "".join(_run(html).text_parts).strip()


def extract_html_links(html: str) -> list[tuple[str, str]]:
    """Return (href, anchor_text) pairs from an HTML body."""
    return _run(html).links
