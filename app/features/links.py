"""Link analysis. Links are only inspected as text. They are never fetched or visited."""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from app.features.domains import is_ip, registered_domain
from app.parsing.html_utils import extract_html_links
from app.parsing.message import Message

URL_RE = re.compile(r"https?://[^\s<>\"')\]]+", re.IGNORECASE)
LOOKS_LIKE_URL_RE = re.compile(r"(?:https?://)?[\w-]+(?:\.[\w-]+)+(?:[/?#]\S*)?", re.IGNORECASE)

SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "buff.ly",
    "rebrand.ly", "cutt.ly", "shorturl.at", "tiny.cc", "rb.gy",
}
SUSPICIOUS_TLDS = {
    "zip", "mov", "top", "xyz", "click", "country", "gq", "tk", "ml", "cf", "ga",
    "work", "support", "loan", "kim", "men", "rest", "icu",
}
MAX_URL_LENGTH = 120
MAX_HOST_LABELS = 5  # e.g. login.secure.paypal.com.evil.example


def defang(url: str) -> str:
    """Make a URL inert for display: hxxp://example[.]com"""
    out = re.sub(r"^http", "hxxp", url, flags=re.IGNORECASE)
    return out.replace(".", "[.]")


def _flags_for(url: str, anchor_text: str = "") -> tuple[str, list[str]]:
    flags: list[str] = []
    try:
        parts = urlsplit(url)
        host = (parts.hostname or "").lower()
    except ValueError:
        return "", ["malformed_url"]
    if not host:
        return "", ["malformed_url"]

    if is_ip(host):
        flags.append("ip_host")
    if host in SHORTENERS:
        flags.append("shortener")
    labels = host.split(".")
    if any(label.startswith("xn--") for label in labels):
        flags.append("punycode")
    if not is_ip(host) and labels[-1] in SUSPICIOUS_TLDS:
        flags.append("suspicious_tld")
    if not is_ip(host) and len(labels) >= MAX_HOST_LABELS:
        flags.append("many_subdomains")
    if len(url) > MAX_URL_LENGTH:
        flags.append("long_url")
    if "@" in parts.netloc:
        flags.append("userinfo_in_url")
    if parts.scheme == "http":
        flags.append("insecure_http")

    anchor = anchor_text.strip()
    if anchor and LOOKS_LIKE_URL_RE.fullmatch(anchor):
        shown = urlsplit(anchor if "://" in anchor else f"//{anchor}").hostname or ""
        if registered_domain(shown) != registered_domain(host):
            flags.append("href_mismatch")
    return host, flags


def analyze_links(message: Message) -> list[dict]:
    """Return one entry per distinct URL: {url (defanged), host, flags}."""
    candidates: list[tuple[str, str]] = []  # (url, anchor text)
    if message.html_body:
        candidates.extend(extract_html_links(message.html_body))
    for text in (message.text_body, message.body_text):
        candidates.extend((u.rstrip(".,;:!?"), "") for u in URL_RE.findall(text))

    results: list[dict] = []
    seen: set[str] = set()
    for url, anchor in candidates:
        if not url.lower().startswith(("http://", "https://")):
            continue  # mailto:, tel:, javascript: and relative links are ignored
        if url in seen:
            continue
        seen.add(url)
        host, flags = _flags_for(url, anchor)
        results.append({"url": defang(url), "host": host, "flags": flags})
    return results
