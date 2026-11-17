"""HTTP fetching helpers shared by the URL importer and image downloader."""

from __future__ import annotations

import ipaddress
import socket

import httpx

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36 Colander/1.0"
)
MAX_PAGE_BYTES = 15 * 1024 * 1024
MAX_REDIRECTS = 10


class FetchError(RuntimeError):
    pass


def resolve_public_host(scheme: str, host: str | None) -> str:
    """Resolve ``host`` and return the address to connect to.

    Rejects non-HTTP schemes and link-local/metadata addresses. LAN addresses are
    allowed on purpose: self-hosters often run other services (e.g. a wiki) on
    their network that they may want to import from.
    """
    if scheme not in ("http", "https") or not host:
        raise FetchError("Only http(s) URLs are supported.")
    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        raise FetchError(f"Could not resolve host {host}") from e
    addresses = [ipaddress.ip_address(info[4][0].split("%", 1)[0]) for info in infos]
    if not addresses:
        raise FetchError(f"Could not resolve host {host}")
    for ip in addresses:
        if ip.is_link_local or ip.is_multicast or ip.is_unspecified:
            raise FetchError("That address is not allowed.")
    return str(addresses[0])


class _PinnedTransport(httpx.HTTPTransport):
    """Connect to the exact address that passed the check, for every request.

    Checking a hostname and then letting the HTTP client resolve it again leaves a
    DNS-rebinding gap: a short-TTL record can answer with a public address for the
    check and a blocked one for the connection. Here the check's address is the
    connection's address. The request keeps its real Host header and TLS still
    verifies the certificate against the real hostname (via SNI), while the client
    above sees the original URL, so cookies and redirects behave normally.
    """

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        url = request.url
        ip = resolve_public_host(url.scheme, url.host)
        extensions = dict(request.extensions)
        if url.scheme == "https":
            extensions["sni_hostname"] = url.host
        pinned = httpx.Request(
            request.method,
            url.copy_with(host=ip),
            headers=request.headers,
            stream=request.stream,
            extensions=extensions,
        )
        return super().handle_request(pinned)


def safe_get(url: str, *, headers: dict[str, str], timeout: float = 30) -> httpx.Response:
    """GET ``url``; every hop, redirects included, is checked and pinned by ``_PinnedTransport``."""
    with httpx.Client(
        transport=_PinnedTransport(),
        follow_redirects=True,
        max_redirects=MAX_REDIRECTS,
        timeout=timeout,
        headers=headers,
    ) as client:
        try:
            return client.get(url)
        except httpx.TooManyRedirects as e:
            raise FetchError("Too many redirects.") from e


def fetch_page(url: str) -> tuple[str, str]:
    """Fetch an HTML page. Returns (final_url, html)."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        r = safe_get(url, headers=headers)
    except httpx.HTTPError as e:
        raise FetchError(f"Could not fetch the page: {e}") from e
    if r.status_code in (401, 403, 429):
        raise FetchError(
            f"The site refused automated access (HTTP {r.status_code}). "
            "Copy the recipe text from your browser and use 'Paste text' instead."
        )
    if r.status_code >= 400:
        raise FetchError(f"The site returned HTTP {r.status_code}.")
    if len(r.content) > MAX_PAGE_BYTES:
        raise FetchError("The page is too large.")
    return str(r.url), r.text
