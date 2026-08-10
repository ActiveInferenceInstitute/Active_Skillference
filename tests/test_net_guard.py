"""Unit coverage for the shared outbound-URL scheme guard."""

from __future__ import annotations

import pytest

from src.net_guard import (
    NonHttpUrlError,
    is_http_url,
    is_loopback_host,
    require_http_url,
)


def test_is_http_url_accepts_http_and_https() -> None:
    assert is_http_url("http://localhost:8080/public/status") is True
    assert is_http_url("https://api.github.com/repos/x/y") is True


def test_is_http_url_rejects_other_schemes() -> None:
    assert is_http_url("file:///etc/passwd") is False
    assert is_http_url("ftp://example.com") is False
    assert is_http_url("not-a-url") is False


def test_require_http_url_returns_url_unchanged_when_valid() -> None:
    url = "http://127.0.0.1:8765/healthz"
    assert require_http_url(url, context="test") == url


def test_require_http_url_raises_with_context_when_invalid() -> None:
    with pytest.raises(NonHttpUrlError, match="test-context.*only http/https URLs"):
        require_http_url("file:///etc/passwd", context="test-context")


def test_is_loopback_host_accepts_localhost_variants() -> None:
    for host in ("localhost", "LOCALHOST", "127.0.0.1", "::1", "[::1]"):
        assert is_loopback_host(host) is True


def test_is_loopback_host_rejects_non_loopback_hosts() -> None:
    for host in ("0.0.0.0", "192.168.1.5", "example.com", ""):
        assert is_loopback_host(host) is False
