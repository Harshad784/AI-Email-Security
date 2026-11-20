"""Rule-based placeholder classifier for Week 1.

It is replaced in Week 2 by the TF-IDF + logistic regression baseline. The interface
(signals in, label / probabilities / uncertain / top signals out) stays the same.
It never outputs "spam" yet: that needs the trained model.
"""
from __future__ import annotations

import math

MODEL_VERSION = "placeholder-0.1.0"

WEIGHTS: dict[str, dict[str, int]] = {
    "sender": {
        "display_name_spoof": 3, "freemail_claims_company": 2, "reply_to_mismatch": 2,
        "return_path_mismatch": 1, "spf_fail": 1, "dkim_fail": 1, "dmarc_fail": 2,
        "missing_from": 1,
    },
    "link": {
        "href_mismatch": 3, "ip_host": 3, "userinfo_in_url": 3, "punycode": 2,
        "shortener": 1, "suspicious_tld": 1, "many_subdomains": 1, "insecure_http": 1,
        "malformed_url": 1,
    },
    "language": {
        "credential_request": 2, "gift_card": 3, "urgency": 1, "payment_request": 1,
        "generic_greeting": 1, "excessive_caps": 1, "excessive_punctuation": 1,
    },
}

UNCERTAIN_LOW, UNCERTAIN_HIGH = 0.3, 0.7


def _collect(signals: dict) -> list[tuple[str, int]]:
    """Each distinct (group, flag) counts once, so one noisy link cannot dominate."""
    found: set[tuple[str, str]] = set()
    for flag in signals["sender"]["flags"]:
        found.add(("sender", flag))
    for link in signals["links"]:
        for flag in link["flags"]:
            found.add(("link", flag))
    for flag in signals["language"]["flags"]:
        found.add(("language", flag))
    scored = [(f"{g}:{f}", WEIGHTS[g].get(f, 0)) for g, f in found]
    return sorted((s for s in scored if s[1] > 0), key=lambda s: (-s[1], s[0]))


def classify(signals: dict) -> dict:
    contributions = _collect(signals)
    score = sum(weight for _, weight in contributions)
    p_phishing = 1 / (1 + math.exp(-(score - 5) * 0.8))
    return {
        "label": "phishing" if p_phishing >= 0.5 else "legitimate",
        "probabilities": {
            "phishing": round(p_phishing, 4),
            "spam": 0.0,
            "legitimate": round(1 - p_phishing, 4),
        },
        "uncertain": UNCERTAIN_LOW <= p_phishing <= UNCERTAIN_HIGH,
        "model_version": MODEL_VERSION,
        "score": score,
        "top_signals": [{"signal": name, "weight": w} for name, w in contributions[:8]],
    }
