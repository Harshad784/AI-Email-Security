"""One entry point used by the API now, and by CSV import and the review queue later."""
from __future__ import annotations

from app.features import extract_signals
from app.models import classify
from app.parsing.message import Message

REASONS = {
    "sender:display_name_spoof": "the sender name does not match the sending domain",
    "sender:freemail_claims_company": "a free email address claims to be a company or role",
    "sender:reply_to_mismatch": "replies would go to a different domain",
    "sender:return_path_mismatch": "the return path domain differs from the sender",
    "sender:spf_fail": "the sender failed the SPF check",
    "sender:dkim_fail": "the sender failed the DKIM check",
    "sender:dmarc_fail": "the sender failed the DMARC check",
    "link:href_mismatch": "a link shows one address but goes to another",
    "link:ip_host": "a link points to a raw IP address",
    "link:userinfo_in_url": "a link hides its real destination after an @ sign",
    "link:punycode": "a link uses look-alike characters in its domain",
    "link:shortener": "a link uses a URL shortener",
    "link:suspicious_tld": "a link uses an unusual domain ending",
    "link:many_subdomains": "a link has an unusually long domain",
    "link:insecure_http": "a link is not encrypted (http)",
    "language:credential_request": "it asks for login or identity details",
    "language:gift_card": "it mentions gift cards",
    "language:urgency": "it pressures you to act quickly",
    "language:payment_request": "it asks for a payment or bank details",
    "language:generic_greeting": "it uses a generic greeting",
    "language:excessive_caps": "it uses excessive capital letters",
    "language:excessive_punctuation": "it uses excessive punctuation",
}


def build_summary(result: dict) -> str:
    reasons = [REASONS[s["signal"]] for s in result["top_signals"] if s["signal"] in REASONS][:3]
    because = "; ".join(reasons)
    if result["uncertain"]:
        return "Not sure about this one, so send it to a reviewer. " + (
            f"Signs found: {because}." if because else ""
        )
    if result["label"] == "phishing":
        return f"Likely phishing, do not click anything and report it: {because}."
    return "No strong signs of phishing found. This is not a guarantee that the email is safe."


def analyze_message(message: Message) -> dict:
    signals = extract_signals(message)
    result = classify(signals)
    return {**result, "summary": build_summary(result), **signals}
