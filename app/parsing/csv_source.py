"""Import emails from a CSV file with row-level error reporting.

Required columns: id, from, to, subject, date, body
Optional columns: headers (raw header block), label
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from email.parser import Parser

from app.config import Settings, get_settings
from app.parsing.eml import ParseError
from app.parsing.message import Message

REQUIRED_COLUMNS = ("id", "from", "to", "subject", "date", "body")


@dataclass(frozen=True)
class RowError:
    row: int  # 1-based row number in the file, header is row 1
    reason: str


def parse_csv_text(
    text: str, *, settings: Settings | None = None
) -> tuple[list[Message], list[RowError]]:
    settings = settings or get_settings()
    if len(text.encode("utf-8", errors="replace")) > settings.max_csv_bytes:
        raise ParseError(f"CSV is larger than the {settings.max_csv_bytes} byte limit")

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ParseError("CSV is empty or has no header row")

    names = {name.strip().lower() for name in reader.fieldnames if name}
    missing = [c for c in REQUIRED_COLUMNS if c not in names]
    if missing:
        raise ParseError(f"CSV is missing required columns: {', '.join(missing)}")

    messages: list[Message] = []
    errors: list[RowError] = []
    row_number = 1
    try:
        for raw_row in reader:
            row_number += 1
            if row_number - 1 > settings.max_csv_rows:
                errors.append(RowError(row_number, "Row limit exceeded; remaining rows skipped"))
                break
            row = {
                (k or "").strip().lower(): (v or "")
                for k, v in raw_row.items()
                if k is not None
            }
            problem = _validate(row)
            if problem:
                errors.append(RowError(row_number, problem))
                continue
            messages.append(_to_message(row))
    except csv.Error as exc:
        errors.append(RowError(row_number + 1, f"Malformed CSV: {exc}"))

    return messages, errors


def _validate(row: dict[str, str]) -> str | None:
    if not row.get("id", "").strip():
        return "Missing 'id'"
    if not row.get("from", "").strip():
        return "Missing 'from'"
    if not row.get("subject", "").strip() and not row.get("body", "").strip():
        return "Both 'subject' and 'body' are empty"
    return None


def _to_message(row: dict[str, str]) -> Message:
    reply_to = return_path = auth = ""
    raw_headers = row.get("headers", "").strip()
    if raw_headers:
        try:
            headers = Parser().parsestr(raw_headers, headersonly=True)
            reply_to = str(headers.get("Reply-To", "") or "")
            return_path = str(headers.get("Return-Path", "") or "")
            auth = "; ".join(str(a) for a in (headers.get_all("Authentication-Results") or []))
        except Exception:
            pass  # bad optional headers must not reject the row
    return Message(
        source="csv",
        message_id=row["id"].strip(),
        from_raw=row["from"].strip(),
        to=row.get("to", "").strip(),
        reply_to=reply_to,
        return_path=return_path,
        subject=row.get("subject", "").strip(),
        date=row.get("date", "").strip(),
        auth_results=auth,
        text_body=row.get("body", "").strip(),
    )
