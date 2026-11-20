"""Runtime settings, read from environment variables on every call (easy to override in tests)."""
from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    # Attachments are off by default. Even when on, v1 only records metadata
    # (filename, type, size, SHA-256) and never opens or renders the contents.
    attachments_enabled: bool
    max_eml_bytes: int
    max_csv_bytes: int
    max_csv_rows: int


def get_settings() -> Settings:
    return Settings(
        attachments_enabled=_env_bool("ATTACHMENTS_ENABLED", False),
        max_eml_bytes=_env_int("MAX_EML_BYTES", 5 * 1024 * 1024),
        max_csv_bytes=_env_int("MAX_CSV_BYTES", 20 * 1024 * 1024),
        max_csv_rows=_env_int("MAX_CSV_ROWS", 10_000),
    )
