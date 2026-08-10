"""Shared outbound-URL guard for local-first CLI tools that call urllib.request.urlopen.

These tools (the learner dashboard, the full-app-stack validator, the console/browser
validators, the curriculum GitHub-tree fetcher) all take their targets from
``--dashboard-url``/``--skilltree-url``/``--base-url`` CLI flags that default to
localhost. Without a scheme check, a caller could pass a ``file://`` or other
non-http(s) URI straight into ``urlopen`` (local file disclosure / SSRF-adjacent).
"""

from __future__ import annotations

import ipaddress
from urllib.parse import urlparse

_ALLOWED_SCHEMES = frozenset({"http", "https"})


class NonHttpUrlError(ValueError):
    """Raised when a URL intended for urlopen is not http or https."""


def is_http_url(url: str) -> bool:
    """Return True if ``url`` uses the http or https scheme."""
    return urlparse(url).scheme in _ALLOWED_SCHEMES


def require_http_url(url: str, *, context: str) -> str:
    """Return ``url`` unchanged if it is http(s); otherwise raise NonHttpUrlError."""
    if not is_http_url(url):
        raise NonHttpUrlError(
            f"{context}: only http/https URLs are supported, got {url!r}"
        )
    return url


def is_loopback_host(host: str) -> bool:
    """Return True if ``host`` names the loopback interface only.

    Accepts the ``localhost`` name and any address inside the IPv4 ``127.0.0.0/8``
    block or the IPv6 ``::1`` loopback. Anything else (a LAN IP, a public hostname,
    ``0.0.0.0``) is rejected.
    """
    candidate = host.strip().strip("[]").lower()
    if candidate == "localhost":
        return True
    try:
        return ipaddress.ip_address(candidate).is_loopback
    except ValueError:
        return False
