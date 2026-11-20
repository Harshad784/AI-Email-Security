"""Parse a raw .eml file into the common Message format."""
from __future__ import annotations

import hashlib
from email import policy
from email.parser import BytesParser

from app.config import Settings, get_settings
from app.parsing.message import Attachment, Message


class ParseError(ValueError):
    """Raised for input that cannot be parsed safely."""


def _header(msg, name: str) -> str:
    try:
        return str(msg.get(name, "") or "").strip()
    except Exception:
        return ""


def _text_of(part) -> str:
    try:
        return part.get_content()
    except Exception:
        payload = part.get_payload(decode=True) or b""
        return payload.decode("utf-8", errors="replace")


def parse_eml_bytes(data: bytes, *, settings: Settings | None = None) -> Message:
    settings = settings or get_settings()
    if not data or not data.strip():
        raise ParseError("Empty email")
    if len(data) > settings.max_eml_bytes:
        raise ParseError(f"Email is larger than the {settings.max_eml_bytes} byte limit")

    try:
        msg = BytesParser(policy=policy.default).parsebytes(data)
    except Exception as exc:
        raise ParseError(f"Could not parse email: {exc}") from exc

    if not msg.keys():
        raise ParseError("No headers found; this does not look like an email")

    text_parts: list[str] = []
    html_parts: list[str] = []
    attachments: list[Attachment] = []

    for part in msg.walk():
        if part.is_multipart():
            continue
        filename = part.get_filename()
        disposition = (part.get_content_disposition() or "").lower()
        if filename or disposition == "attachment":
            # Metadata only: hash the raw bytes, never interpret or render them.
            payload = part.get_payload(decode=True) or b""
            attachments.append(
                Attachment(
                    filename=str(filename or "(unnamed)"),
                    content_type=part.get_content_type(),
                    size=len(payload),
                    sha256=hashlib.sha256(payload).hexdigest(),
                )
            )
            continue
        ctype = part.get_content_type()
        if ctype == "text/plain":
            text_parts.append(_text_of(part))
        elif ctype == "text/html":
            html_parts.append(_text_of(part))

    auth = msg.get_all("Authentication-Results") or []

    return Message(
        source="eml",
        message_id=_header(msg, "Message-ID"),
        from_raw=_header(msg, "From"),
        to=_header(msg, "To"),
        reply_to=_header(msg, "Reply-To"),
        return_path=_header(msg, "Return-Path"),
        subject=_header(msg, "Subject"),
        date=_header(msg, "Date"),
        auth_results="; ".join(str(a) for a in auth),
        text_body="\n".join(text_parts).strip(),
        html_body="\n".join(html_parts).strip(),
        attachments=attachments,
    )
