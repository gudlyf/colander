"""Redirects must be re-checked so a public URL can't bounce into a blocked address."""

import httpx
import pytest

from app.services import fetch


def _client_factory(handler):
    real = httpx.Client

    def make(**kw):
        return real(transport=httpx.MockTransport(handler), **kw)

    return make


def test_redirect_to_metadata_endpoint_is_blocked(monkeypatch):
    def handler(request):
        return httpx.Response(302, headers={"location": "http://169.254.169.254/latest/meta-data/"})

    monkeypatch.setattr(fetch.httpx, "Client", _client_factory(handler))
    monkeypatch.setattr(fetch, "assert_public_url", _fake_assert)
    with pytest.raises(fetch.FetchError):
        fetch.safe_get("http://example.com/x", headers={})


def test_redirects_are_followed(monkeypatch):
    def handler(request):
        if request.url.path == "/start":
            return httpx.Response(301, headers={"location": "/end"})
        return httpx.Response(200, text="ok")

    monkeypatch.setattr(fetch.httpx, "Client", _client_factory(handler))
    monkeypatch.setattr(fetch, "assert_public_url", _fake_assert)
    r = fetch.safe_get("http://example.com/start", headers={})
    assert r.status_code == 200
    assert str(r.url) == "http://example.com/end"


def test_redirect_loop_gives_up(monkeypatch):
    def handler(request):
        return httpx.Response(302, headers={"location": "/again"})

    monkeypatch.setattr(fetch.httpx, "Client", _client_factory(handler))
    monkeypatch.setattr(fetch, "assert_public_url", _fake_assert)
    with pytest.raises(fetch.FetchError, match="Too many redirects"):
        fetch.safe_get("http://example.com/", headers={})


def _fake_assert(url: str) -> None:
    """assert_public_url without DNS: only the link-local metadata host is blocked."""
    if "169.254." in url:
        raise fetch.FetchError("That address is not allowed.")
