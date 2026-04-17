from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.tools.web_fetch_tool import _call, _strip_html


# --- _strip_html unit tests ---

def test_strip_html_removes_tags():
    assert "<p>" not in _strip_html("<p>hello</p>")
    assert "hello" in _strip_html("<p>hello</p>")


def test_strip_html_removes_script():
    result = _strip_html("<script>alert(1)</script>text")
    assert "alert" not in result
    assert "text" in result


def test_strip_html_removes_style():
    result = _strip_html("<style>body{color:red}</style>text")
    assert "color" not in result
    assert "text" in result


def test_strip_html_decodes_entities():
    assert "&" in _strip_html("&amp;")
    assert "<" in _strip_html("&lt;")
    assert ">" in _strip_html("&gt;")


# --- _call tests ---

def _mock_response(text="hello", content_type="text/plain", status=200):
    resp = MagicMock()
    resp.text = text
    resp.headers = {"content-type": content_type}
    resp.status_code = status
    resp.raise_for_status = MagicMock()
    return resp


def _mock_client(resp):
    client = AsyncMock()
    client.get = AsyncMock(return_value=resp)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


async def test_fetch_plain_text(ctx):
    with patch("src.tools.web_fetch_tool.httpx.AsyncClient", return_value=_mock_client(_mock_response("hello"))):
        result = await _call({"url": "http://example.com"}, ctx)
    assert "hello" in result.content[0]["text"]
    assert not result.is_error


async def test_fetch_strips_html(ctx):
    html = "<html><body><p>content</p></body></html>"
    resp = _mock_response(text=html, content_type="text/html")
    with patch("src.tools.web_fetch_tool.httpx.AsyncClient", return_value=_mock_client(resp)):
        result = await _call({"url": "http://example.com"}, ctx)
    assert "<p>" not in result.content[0]["text"]
    assert "content" in result.content[0]["text"]


async def test_fetch_http_error(ctx):
    resp = MagicMock()
    resp.status_code = 404
    resp.headers = {"content-type": "text/plain"}
    http_err = httpx.HTTPStatusError("not found", request=MagicMock(), response=resp)
    resp.raise_for_status = MagicMock(side_effect=http_err)
    with patch("src.tools.web_fetch_tool.httpx.AsyncClient", return_value=_mock_client(resp)):
        result = await _call({"url": "http://example.com/missing"}, ctx)
    assert result.is_error
    assert "404" in result.content[0]["text"]


async def test_fetch_network_error(ctx):
    client = AsyncMock()
    client.get = AsyncMock(side_effect=Exception("connection refused"))
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    with patch("src.tools.web_fetch_tool.httpx.AsyncClient", return_value=client):
        result = await _call({"url": "http://bad.example"}, ctx)
    assert result.is_error
    assert "connection refused" in result.content[0]["text"]


async def test_fetch_start_index(ctx):
    resp = _mock_response("abcdefghij", content_type="text/plain")
    with patch("src.tools.web_fetch_tool.httpx.AsyncClient", return_value=_mock_client(resp)):
        result = await _call({"url": "http://x.com", "start_index": 5, "max_length": 5}, ctx)
    assert result.content[0]["text"] == "fghij"


async def test_fetch_max_length(ctx):
    resp = _mock_response("a" * 200, content_type="text/plain")
    with patch("src.tools.web_fetch_tool.httpx.AsyncClient", return_value=_mock_client(resp)):
        result = await _call({"url": "http://x.com", "max_length": 10}, ctx)
    assert len(result.content[0]["text"]) <= 10
