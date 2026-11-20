from app.features import extract_signals
from app.features.domains import registered_domain
from app.features.links import defang
from tests.helpers import load


def _link_flags(signals):
    return {f for link in signals["links"] for f in link["flags"]}


def test_registered_domain_helper():
    assert registered_domain("login.paypal.com") == "paypal.com"
    assert registered_domain("a.b.example.co.uk") == "example.co.uk"
    assert registered_domain("198.51.100.7") == "198.51.100.7"


def test_defang_makes_urls_inert():
    out = defang("http://evil.example.com/login")
    assert out == "hxxp://evil[.]example[.]com/login"
    assert "http://" not in out


def test_phish_link_flags():
    flags = _link_flags(extract_signals(load("phish_credential.eml")))
    assert {"ip_host", "href_mismatch", "insecure_http"} <= flags


def test_phish_sender_flags():
    sender = extract_signals(load("phish_credential.eml"))["sender"]
    assert {"reply_to_mismatch", "return_path_mismatch", "display_name_spoof",
            "spf_fail", "dmarc_fail"} <= set(sender["flags"])
    assert sender["spf"] == "fail" and sender["dmarc"] == "fail"


def test_phish_language_flags():
    language = extract_signals(load("phish_credential.eml"))["language"]
    assert {"urgency", "credential_request", "generic_greeting"} <= set(language["flags"])


def test_ham_has_no_flags():
    signals = extract_signals(load("ham_meeting.eml"))
    assert signals["sender"]["flags"] == []
    assert signals["language"]["flags"] == []
    assert signals["links"] == []
    assert signals["sender"]["spf"] == "pass"


def test_spam_sample_flags():
    signals = extract_signals(load("spam_marketing.eml"))
    assert "shortener" in _link_flags(signals)
    assert {"excessive_caps", "excessive_punctuation"} <= set(signals["language"]["flags"])


def test_attachment_metadata_in_signals():
    signals = extract_signals(load("with_attachment.eml"))
    assert signals["attachments"][0]["filename"] == "invoice.pdf"
    assert len(signals["attachments"][0]["sha256"]) == 64


def test_freemail_claiming_company():
    from app.parsing.message import Message

    msg = Message(from_raw='"Microsoft Support" <help.desk@gmail.com>')
    assert "freemail_claims_company" in extract_signals(msg)["sender"]["flags"]


def test_lookalike_and_userinfo_links():
    from app.parsing.message import Message

    msg = Message(text_body="Go to http://xn--pypal-4ve.com/login or http://paypal.com@evil.example.xyz/a")
    flags = _link_flags(extract_signals(msg))
    assert {"punycode", "userinfo_in_url", "suspicious_tld"} <= flags


def test_mailto_and_javascript_links_ignored():
    from app.parsing.message import Message

    msg = Message(html_body='<a href="mailto:a@example.com">mail</a><a href="javascript:alert(1)">x</a>')
    assert extract_signals(msg)["links"] == []
