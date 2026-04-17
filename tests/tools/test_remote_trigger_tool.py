from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tools.remote_trigger_tool import _call


def _mock_response(status=200, json_data=None, text="", raise_exc=None):
    resp = MagicMock()
    resp.status_code = status
    resp.text = text
    if json_data is not None:
        resp.json = MagicMock(return_value=json_data)
    else:
        resp.json = MagicMock(side_effect=Exception("not json"))
    if raise_exc:
        resp.raise_for_status = MagicMock(side_effect=raise_exc)
    else:
        resp.raise_for_status = MagicMock()
    return resp


def _patch_client(resp):
    client = AsyncMock()
    client.post = AsyncMock(return_value=resp)
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=client)
    cm.__aexit__ = AsyncMock(return_value=False)
    return patch("src.tools.remote_trigger_tool.httpx.AsyncClient", return_value=cm)


async def test_successful_json_response(ctx):
    resp = _mock_response(status=200, json_data={"ok": True})
    with _patch_client(resp):
        result = await _call({"url": "http://example.com/hook"}, ctx)
    assert "200" in result.content[0]["text"]
    assert '"ok"' in result.content[0]["text"]
    assert not result.is_error


async def test_successful_text_response(ctx):
    resp = _mock_response(status=200, text="plain text")
    with _patch_client(resp):
        result = await _call({"url": "http://x.com"}, ctx)
    assert "plain text" in result.content[0]["text"]


async def test_http_error_returns_error(ctx):
    with patch(
        "src.tools.remote_trigger_tool.httpx.AsyncClient",
        side_effect=Exception("connection refused"),
    ):
        result = await _call({"url": "http://bad"}, ctx)
    assert result.is_error
    assert "connection refused" in result.content[0]["text"]


async def test_payload_and_headers_forwarded(ctx):
    resp = _mock_response(json_data={})
    client = AsyncMock()
    client.post = AsyncMock(return_value=resp)
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=client)
    cm.__aexit__ = AsyncMock(return_value=False)
    with patch("src.tools.remote_trigger_tool.httpx.AsyncClient", return_value=cm):
        await _call(
            {"url": "http://x.com", "payload": {"k": "v"}, "headers": {"X-Auth": "t"}},
            ctx,
        )
    client.post.assert_awaited_once_with(
        "http://x.com", json={"k": "v"}, headers={"X-Auth": "t"}
    )
