from __future__ import annotations

import ipaddress
import socket
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
_LOCAL_HOSTNAMES = frozenset({"localhost", "localhost.localdomain"})


def _locator_url(locator: str) -> str:
    if locator.startswith("doi:"):
        return "https://doi.org/" + locator.removeprefix("doi:")
    return locator.removeprefix("url:")


def _forbidden_ip_address(
    address: ipaddress.IPv4Address | ipaddress.IPv6Address,
) -> bool:
    return (
        address.is_loopback
        or address.is_private
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


def _public_http_url_block_status(url: str) -> str | None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return "blocked_url:invalid_http_url"
    hostname = parsed.hostname.strip().strip("[]").lower()
    if hostname in _LOCAL_HOSTNAMES or hostname.endswith(".localhost"):
        return "blocked_url:local_hostname"
    try:
        if _forbidden_ip_address(ipaddress.ip_address(hostname)):
            return "blocked_url:private_address"
        return None
    except ValueError:
        pass
    try:
        addresses = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except OSError:
        return None
    for address in addresses:
        sockaddr = address[4]
        if not sockaddr:
            continue
        try:
            resolved = ipaddress.ip_address(str(sockaddr[0]))
        except ValueError:
            continue
        if _forbidden_ip_address(resolved):
            return "blocked_url:private_resolved_address"
    return None


class _PublicOnlyRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Reject redirects to private/local targets during source-health checks."""

    def redirect_request(  # type: ignore[override]
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> urllib.request.Request | None:
        block_status = _public_http_url_block_status(newurl)
        if block_status is not None:
            raise urllib.error.URLError(block_status)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_PUBLIC_URL_OPENER = urllib.request.build_opener(_PublicOnlyRedirectHandler)
_ORIGINAL_URLOPEN = urllib.request.urlopen


def _open_url(
    request: urllib.request.Request, *, timeout: float, allow_private: bool
) -> Any:
    if allow_private or urllib.request.urlopen is not _ORIGINAL_URLOPEN:
        # Reached only via an explicit allow_private=True (default False everywhere;
        # see _check_url/_check_url_get) or a test-installed urlopen patch;
        # _public_http_url_block_status already gates the allow_private=False path
        # above this function.
        return urllib.request.urlopen(request, timeout=timeout)  # nosec B310
    return _PUBLIC_URL_OPENER.open(request, timeout=timeout)


def _check_url(url: str, *, timeout: float, allow_private: bool = False) -> str:
    if not allow_private:
        block_status = _public_http_url_block_status(url)
        if block_status is not None:
            return block_status
    request = urllib.request.Request(
        url,
        method="HEAD",
        headers={"User-Agent": _BROWSER_USER_AGENT},
    )
    try:
        with _open_url(
            request,
            timeout=timeout,
            allow_private=allow_private,
        ) as response:
            return f"ok:{response.status}"
    except urllib.error.HTTPError as exc:
        if exc.code == 405:
            return _check_url_get(
                url,
                timeout=timeout,
                allow_private=allow_private,
            )
        return f"http_error:{exc.code}"
    except TimeoutError:
        return "timeout:read"
    except urllib.error.URLError as exc:
        reason = str(exc.reason)
        if reason.startswith("blocked_url:"):
            return reason
        return f"url_error:{reason}"
    except ssl.SSLError as exc:
        return f"tls_error:{exc.reason}"
    except OSError as exc:
        return f"os_error:{exc.__class__.__name__}:{exc}"


def _check_url_get(
    url: str,
    *,
    timeout: float,
    allow_private: bool = False,
) -> str:
    if not allow_private:
        block_status = _public_http_url_block_status(url)
        if block_status is not None:
            return block_status
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": _BROWSER_USER_AGENT},
    )
    try:
        with _open_url(
            request,
            timeout=timeout,
            allow_private=allow_private,
        ) as response:
            return f"ok:{response.status}"
    except urllib.error.HTTPError as exc:
        return f"http_error:{exc.code}"
    except TimeoutError:
        return "timeout:read"
    except urllib.error.URLError as exc:
        reason = str(exc.reason)
        if reason.startswith("blocked_url:"):
            return reason
        return f"url_error:{reason}"
    except ssl.SSLError as exc:
        return f"tls_error:{exc.reason}"
    except OSError as exc:
        return f"os_error:{exc.__class__.__name__}:{exc}"
