"""
SSRF guards for outbound HTTP from user-influenced URLs (queue rows, pipeline input).

Blocks private/reserved IPs, link-local, loopback, and the GCE metadata endpoints.
"""
from __future__ import annotations

import ipaddress
import re
import socket
from urllib.parse import urlparse

_BLOCKED_HOSTS = frozenset({"metadata.google.internal", "metadata.goog"})
_DOI_RE = re.compile(r"^10\.\d{4,}/\S+$", re.IGNORECASE)
_MAX_REDIRECTS = 5


def _hostname_resolves_to_blocked_ip(hostname: str) -> bool:
    try:
        infos = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        # Unresolved host — defer to httpx (verify_source handles network errors)
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or str(ip) == "169.254.169.254"
        ):
            return True
    return False


def is_safe_outbound_url(url: str) -> bool:
    """Return True if url is an allowed https target for user-influenced fetches."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme != "https":
        return False
    hostname = parsed.hostname
    if not hostname:
        return False
    host = hostname.lower()
    if host in _BLOCKED_HOSTS:
        return False
    if host == "localhost" or host.endswith(".localhost"):
        return False
    # Literal IP in URL
    try:
        ip = ipaddress.ip_address(host)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or str(ip) == "169.254.169.254"
        ):
            return False
    except ValueError:
        pass
    return not _hostname_resolves_to_blocked_ip(host)


def normalise_doi(doi: str) -> str | None:
    """Validate DOI shape before building https://doi.org/{doi}."""
    d = doi.strip().removeprefix("https://doi.org/").removeprefix("http://doi.org/")
    if not d or ".." in d or not _DOI_RE.match(d):
        return None
    return d


def safe_https_url(url: str | None) -> str | None:
    if not url:
        return None
    return url if is_safe_outbound_url(url) else None
