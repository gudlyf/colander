"""Every request, redirects included, must connect to the address that passed the check."""

import socket

import httpx
import pytest

from app.services import fetch

DNS = {
    "example.com": ["93.184.216.34"],
    "wiki.lan": ["192.168.1.20"],
    "metadata.evil": ["169.254.169.254"],
    "mixed.evil": ["93.184.216.35", "169.254.169.254"],
    "v6.example": ["2001:db8::1"],
}


@pytest.fixture
def net(monkeypatch):
    """Fake DNS plus a fake wire that records what the pinned transport actually sends."""
    sent: list[httpx.Request] = []
    routes: dict[str, callable] = {}

    def getaddrinfo(host, port, *args, **kwargs):
        if host not in DNS:
            raise socket.gaierror("unknown host")
        return [(None, None, None, "", (ip, 0)) for ip in DNS[host]]

    def wire(self, request):
        sent.append(request)
        handler = routes.get(request.headers["host"] + request.url.path)
        return handler(request) if handler else httpx.Response(200, text="ok")

    monkeypatch.setattr(fetch.socket, "getaddrinfo", getaddrinfo)
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", wire)
    return sent, routes


def test_connects_to_checked_ip_with_real_host_and_sni(net):
    sent, _ = net
    r = fetch.safe_get("https://example.com/recipe", headers={})
    assert r.status_code == 200
    assert str(r.url) == "https://example.com/recipe"  # callers see the real URL
    (req,) = sent
    assert req.url.host == "93.184.216.34"
    assert req.headers["host"] == "example.com"
    assert req.extensions["sni_hostname"] == "example.com"


def test_ipv6_address_is_bracketed(net):
    sent, _ = net
    fetch.safe_get("http://v6.example:8080/x", headers={})
    assert str(sent[0].url) == "http://[2001:db8::1]:8080/x"
    assert sent[0].headers["host"] == "v6.example:8080"
    assert "sni_hostname" not in sent[0].extensions


def test_lan_addresses_are_allowed(net):
    assert fetch.safe_get("http://wiki.lan/page", headers={}).status_code == 200


@pytest.mark.parametrize(
    "url",
    [
        "http://metadata.evil/",
        "http://mixed.evil/",
        "http://169.254.169.254/latest/meta-data/",
        "http://[fe80::1]/",
    ],
)
def test_blocked_addresses_never_connect(net, url):
    sent, _ = net
    with pytest.raises(fetch.FetchError):
        fetch.safe_get(url, headers={})
    assert sent == []


def test_redirect_to_metadata_endpoint_is_blocked(net):
    sent, routes = net
    routes["example.com/x"] = lambda r: httpx.Response(
        302, headers={"location": "http://169.254.169.254/latest/meta-data/"}
    )
    with pytest.raises(fetch.FetchError):
        fetch.safe_get("http://example.com/x", headers={})
    assert len(sent) == 1


def test_dns_rebinding_cannot_swap_the_connection_address(net, monkeypatch):
    """Even if DNS answers differently on a second lookup, we only resolve once per hop."""
    sent, _ = net
    answers = iter([["93.184.216.34"], ["169.254.169.254"]])
    real = fetch.socket.getaddrinfo

    def flip(host, *a, **kw):
        if host == "rebind.evil":
            return [(None, None, None, "", (ip, 0)) for ip in next(answers)]
        return real(host, *a, **kw)

    monkeypatch.setattr(fetch.socket, "getaddrinfo", flip)
    fetch.safe_get("http://rebind.evil/", headers={})
    assert sent[0].url.host == "93.184.216.34"


def test_redirects_keep_real_url_and_cookies(net):
    sent, routes = net
    routes["example.com/start"] = lambda r: httpx.Response(
        302, headers={"location": "/end", "set-cookie": "consent=yes; Path=/"}
    )
    r = fetch.safe_get("http://example.com/start", headers={})
    assert str(r.url) == "http://example.com/end"
    assert sent[1].headers.get("cookie") == "consent=yes"


def test_redirect_loop_gives_up(net):
    _, routes = net
    routes["example.com/"] = lambda r: httpx.Response(302, headers={"location": "/"})
    with pytest.raises(fetch.FetchError, match="Too many redirects"):
        fetch.safe_get("http://example.com/", headers={})


def test_non_http_scheme_rejected(net):
    with pytest.raises(fetch.FetchError):
        fetch.safe_get("ftp://example.com/", headers={})
