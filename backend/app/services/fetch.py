"""HTTP fetching helpers shared by the URL importer and image downloader."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

import httpx

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36 Colander/1.0"
)
MAX_PAGE_BYTES = 15 * 1024 * 1024
MAX_REDIRECTS = 10


class FetchError(RuntimeError):
    pass


def assert_public_url(url: str) -> None:
    """Reject non-HTTP schemes and link-local/metadata addresses.

    LAN addresses are allowed on purpose: self-hosters often run other services
    (e.g. a wiki) on their network that they may want to import from.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise FetchError("Only http(s) URLs are supported.")
    try:
        infos = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror as e:
        raise FetchError(f"Could not resolve host {parsed.hostname}") from e
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_link_local or ip.is_multicast or ip.is_unspecified:
            raise FetchError("That address is not allowed.")


def safe_get(url: str, *, headers: dict[str, str], timeout: float = 30) -> httpx.Response:
    """GET ``url``, following redirects ourselves so every hop passes ``assert_public_url``.

    httpx's ``follow_redirects=True`` would happily chase a public URL into a
    blocked address (e.g. the cloud metadata endpoint), so we don't use it.
    """
    with httpx.Client(follow_redirects=False, timeout=timeout, headers=headers) as client:
        for _ in range(MAX_REDIRECTS + 1):
            assert_public_url(url)
            r = client.get(url)
            if not r.is_redirect:
                return r
            url = str(r.url.join(r.headers["location"]))
    raise FetchError("Too many redirects.")


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
