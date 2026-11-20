"""Sender analysis from headers. Uses only data present in the email."""
from __future__ import annotations

import re
from email.utils import parseaddr

from app.features.domains import FREEMAIL_DOMAINS, registered_domain
from app.parsing.message import Message

BRANDS = {
    "paypal", "microsoft", "apple", "amazon", "google", "netflix", "dhl",
    "fedex", "docusign", "office365", "linkedin", "facebook", "bank",
}
ROLES = {
    "support", "security", "helpdesk", "it department", "accounts", "billing",
    "hr", "ceo", "director", "admin", "payroll",
}
EMAIL_IN_TEXT_RE = re.compile(r"[\w.+-]+@([\w-]+(?:\.[\w-]+)+)")


def _domain(addr: str) -> str:
    return addr.rsplit("@", 1)[1].lower().strip(">") if "@" in addr else ""


def parse_auth_results(text: str) -> dict[str, str | None]:
    out: dict[str, str | None] = {"spf": None, "dkim": None, "dmarc": None}
    for key in out:
        match = re.search(rf"\b{key}\s*=\s*(\w+)", text or "", re.IGNORECASE)
        if match:
            out[key] = match.group(1).lower()
    return out


def analyze_sender(message: Message) -> dict:
    name, addr = parseaddr(message.from_raw)
    from_domain = _domain(addr)
    from_reg = registered_domain(from_domain)
    flags: list[str] = []

    if not addr:
        flags.append("missing_from")

    _, reply_addr = parseaddr(message.reply_to)
    reply_domain = _domain(reply_addr)
    if reply_domain and registered_domain(reply_domain) != from_reg:
        flags.append("reply_to_mismatch")

    _, return_addr = parseaddr(message.return_path)
    return_domain = _domain(return_addr)
    if return_domain and registered_domain(return_domain) != from_reg:
        flags.append("return_path_mismatch")

    name_l = name.lower()
    spoofed = False
    embedded = EMAIL_IN_TEXT_RE.search(name_l)
    if embedded and registered_domain(embedded.group(1)) != from_reg:
        spoofed = True
    if any(brand in name_l for brand in BRANDS) and not any(
        brand in from_domain for brand in BRANDS if brand in name_l
    ):
        spoofed = True
    if spoofed:
        flags.append("display_name_spoof")

    if from_domain in FREEMAIL_DOMAINS and (
        any(brand in name_l for brand in BRANDS)
        or any(re.search(rf"\b{re.escape(role)}\b", name_l) for role in ROLES)
    ):
        flags.append("freemail_claims_company")

    auth = parse_auth_results(message.auth_results)
    if auth["spf"] in {"fail", "softfail"}:
        flags.append("spf_fail")
    if auth["dkim"] == "fail":
        flags.append("dkim_fail")
    if auth["dmarc"] == "fail":
        flags.append("dmarc_fail")

    return {
        "from_name": name,
        "from_address": addr,
        "reply_to": reply_addr,
        "return_path": return_addr,
        "spf": auth["spf"],
        "dkim": auth["dkim"],
        "dmarc": auth["dmarc"],
        "flags": flags,
    }
