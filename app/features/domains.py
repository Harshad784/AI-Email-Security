"""Small domain helpers shared by the link and sender checks (no network, no external data)."""
from __future__ import annotations

import ipaddress

# Common two-level public suffixes. A full public-suffix list can replace this later.
TWO_LEVEL_SUFFIXES = {
    "co.uk", "org.uk", "ac.uk", "gov.uk", "com.au", "net.au", "org.au",
    "co.in", "net.in", "org.in", "co.jp", "com.br", "com.cn", "co.nz", "co.za",
}

FREEMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "live.com", "aol.com",
    "icloud.com", "proton.me", "protonmail.com", "gmx.com", "mail.com", "yandex.com",
}


def is_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host.strip("[]"))
        return True
    except ValueError:
        return False


def registered_domain(host: str) -> str:
    """Approximate registered domain: example.co.uk for a.b.example.co.uk."""
    host = host.lower().strip(".")
    if not host or is_ip(host):
        return host
    labels = host.split(".")
    if len(labels) <= 2:
        return host
    if ".".join(labels[-2:]) in TWO_LEVEL_SUFFIXES and len(labels) >= 3:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])
