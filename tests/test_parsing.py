import hashlib

from app.config import Settings
from app.parsing import ParseError, parse_csv_text, parse_eml_bytes
from tests.helpers import load


def _settings(**kw):
    base = dict(attachments_enabled=False, max_eml_bytes=5_000_000, max_csv_bytes=5_000_000,
                max_csv_rows=10_000)
    base.update(kw)
    return Settings(**base)


def test_parse_basic_headers_and_body():
    msg = load("ham_meeting.eml")
    assert msg.from_raw == "Alice Smith <alice@example.com>"
    assert msg.subject == "Weekly planning meeting"
    assert "planning meeting" in msg.text_body
    assert "spf=pass" in msg.auth_results


def test_parse_multipart_keeps_text_and_html():
    msg = load("phish_credential.eml")
    assert "suspended" in msg.text_body
    assert "<a href" in msg.html_body


def test_attachment_is_metadata_only():
    msg = load("with_attachment.eml")
    assert len(msg.attachments) == 1
    att = msg.attachments[0]
    assert att.filename == "invoice.pdf"
    assert att.content_type == "application/pdf"
    expected = b"%PDF-1.4 fake attachment content for tests"
    assert att.size == len(expected)
    assert att.sha256 == hashlib.sha256(expected).hexdigest()
    assert not hasattr(att, "content")
    assert "fake attachment content" not in msg.body_text


def test_empty_and_garbage_input_rejected():
    for bad in (b"", b"   \n", b"just some text with no headers at all"):
        try:
            parse_eml_bytes(bad)
        except ParseError:
            continue
        raise AssertionError(f"expected ParseError for {bad!r}")


def test_size_limit_enforced():
    try:
        parse_eml_bytes(b"From: a@example.com\n\n" + b"x" * 200, settings=_settings(max_eml_bytes=50))
    except ParseError as exc:
        assert "limit" in str(exc)
    else:
        raise AssertionError("expected ParseError")


def test_content_hash_is_stable_for_duplicates():
    assert load("ham_meeting.eml").content_hash == load("ham_meeting.eml").content_hash
    assert load("ham_meeting.eml").content_hash != load("spam_marketing.eml").content_hash


def _csv(rows):
    header = "id,from,to,subject,date,body\n"
    return header + "\n".join(rows) + "\n"


def test_csv_one_bad_row_out_of_100_gives_99_messages_and_one_error():
    rows = [f"{i},a{i}@example.com,b@example.com,Subject {i},2026-11-16,Body {i}" for i in range(1, 101)]
    rows[49] = ",missing-id@example.com,b@example.com,Subject,2026-11-16,Body"
    messages, errors = parse_csv_text(_csv(rows))
    assert len(messages) == 99
    assert len(errors) == 1
    assert errors[0].row == 51  # header is row 1, so data row 50 is file row 51
    assert "id" in errors[0].reason


def test_csv_missing_required_column_rejected():
    try:
        parse_csv_text("id,from,subject\n1,a@example.com,Hi\n")
    except ParseError as exc:
        assert "to" in str(exc) and "body" in str(exc)
    else:
        raise AssertionError("expected ParseError")


def test_csv_row_limit():
    rows = [f"{i},a@example.com,b@example.com,S,2026-11-16,B" for i in range(1, 11)]
    messages, errors = parse_csv_text(_csv(rows), settings=_settings(max_csv_rows=5))
    assert len(messages) == 5
    assert any("limit" in e.reason.lower() for e in errors)


def test_csv_optional_headers_column_is_used():
    text = 'id,from,to,subject,date,body,headers\n1,a@example.com,b@example.com,S,d,B,"Reply-To: x@evil.test\nAuthentication-Results: x; spf=fail"\n'
    messages, errors = parse_csv_text(text)
    assert not errors
    assert messages[0].reply_to == "x@evil.test"
    assert "spf=fail" in messages[0].auth_results
