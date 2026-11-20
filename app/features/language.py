"""Language signals: simple, transparent phrase and style checks."""
from __future__ import annotations

import re

from app.parsing.message import Message

PHRASES: dict[str, list[str]] = {
    "urgency": [
        "urgent", "immediately", "act now", "within 24 hours", "within 48 hours",
        "final notice", "last warning", "account suspended", "will be suspended",
        "will be closed", "expires today", "verify now", "action required",
    ],
    "credential_request": [
        "verify your account", "verify your identity", "confirm your identity",
        "confirm your account", "update your password", "reset your password",
        "your password", "sign in to", "log in to", "login to", "one-time code",
        "verification code", "social security", "security question", "account number",
    ],
    "payment_request": [
        "wire transfer", "bank details", "bank account", "routing number",
        "payment details", "outstanding invoice", "pay immediately", "bitcoin",
        "cryptocurrency", "western union", "change of bank",
    ],
    "gift_card": [
        "gift card", "itunes card", "google play card", "steam card", "amazon card",
    ],
    "generic_greeting": [
        "dear customer", "dear user", "dear client", "dear member",
        "dear account holder", "dear sir", "dear madam", "dear valued", "dear friend",
    ],
}
EXCESSIVE_PUNCT_RE = re.compile(r"[!?]{3,}")


def analyze_language(message: Message) -> dict:
    text = f"{message.subject}\n{message.body_text}"
    lowered = text.lower()

    flags: list[str] = []
    matches: dict[str, list[str]] = {}
    for category, phrases in PHRASES.items():
        found = [p for p in phrases if p in lowered]
        if found:
            flags.append(category)
            matches[category] = found

    letters = [c for c in text if c.isalpha()]
    if len(letters) >= 20 and sum(c.isupper() for c in letters) / len(letters) > 0.5:
        flags.append("excessive_caps")
    if EXCESSIVE_PUNCT_RE.search(text):
        flags.append("excessive_punctuation")

    top_terms = [term for terms in matches.values() for term in terms][:8]
    return {"flags": flags, "matches": matches, "top_terms": top_terms}
