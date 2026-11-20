"""Common message format used by every input source (EML, CSV, later Microsoft 365)."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from app.parsing.html_utils import html_to_text


@dataclass(frozen=True)
class Attachment:
    """Metadata only. The attachment contents are never stored, opened, or rendered."""

    filename: str
    content_type: str
    size: int
    sha256: str


@dataclass
class Message:
    source: str = "unknown"
    message_id: str = ""
    from_raw: str = ""
    to: str = ""
    reply_to: str = ""
    return_path: str = ""
    subject: str = ""
    date: str = ""
    auth_results: str = ""
    text_body: str = ""
    html_body: str = ""
    attachments: list[Attachment] = field(default_factory=list)

    @property
    def body_text(self) -> str:
        """Plain text used for language analysis. HTML is converted to inert text."""
        parts = [self.text_body]
        if self.html_body:
            parts.append(html_to_text(self.html_body))
        return "\n".join(p for p in parts if p).strip()

    @property
    def content_hash(self) -> str:
        """Stable hash for de-duplication."""
        raw = "\x1f".join([self.from_raw, self.subject, self.body_text])
        return hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()
