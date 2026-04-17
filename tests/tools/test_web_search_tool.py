from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tools.web_search_tool import _call


def _make_client(texts=("search result",), raise_exc=None):
    block = MagicMock()
    block.text = texts[0]
    response = MagicMock()
    response.content = [block] if not raise_exc else []

    client = MagicMock()
    if raise_exc:
        client.beta.messages.create = AsyncMock(side_effect=raise_exc)
    else:
        client.beta.messages.create = AsyncMock(return_value=response)
    return client


def _patch_anthropic(client):
    from unittest.mock import patch as _patch
    import contextlib

    @contextlib.contextmanager
    def _ctx():
        with patch("anthropic.AsyncAnthropic", return_value=client), \
             patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            yield

    return _ctx()


async def test_search_returns_text(ctx):
    client = _make_client(texts=("Python is great",))
    with _patch_anthropic(client):
        result = await _call({"query": "Python"}, ctx)
    assert "Python is great" in result.content[0]["text"]
    assert not result.is_error


async def test_search_no_text_blocks(ctx):
    response = MagicMock()
    response.content = []
    client = MagicMock()
    client.beta.messages.create = AsyncMock(return_value=response)
    with _patch_anthropic(client):
        result = await _call({"query": "anything"}, ctx)
    assert result.content[0]["text"] == "(no results)"


async def test_search_exception_returns_error(ctx):
    client = _make_client(raise_exc=Exception("API down"))
    with _patch_anthropic(client):
        result = await _call({"query": "test"}, ctx)
    assert result.is_error
    assert "API down" in result.content[0]["text"]


async def test_search_passes_allowed_domains(ctx):
    client = _make_client()
    with _patch_anthropic(client):
        await _call({"query": "x", "allowed_domains": ["example.com"]}, ctx)
    call_kwargs = client.beta.messages.create.call_args[1]
    tools = call_kwargs["tools"]
    assert tools[0].get("allowed_domains") == ["example.com"]


async def test_search_passes_blocked_domains(ctx):
    client = _make_client()
    with _patch_anthropic(client):
        await _call({"query": "x", "blocked_domains": ["spam.com"]}, ctx)
    call_kwargs = client.beta.messages.create.call_args[1]
    tools = call_kwargs["tools"]
    assert tools[0].get("blocked_domains") == ["spam.com"]


async def test_search_no_domain_filters_by_default(ctx):
    client = _make_client()
    with _patch_anthropic(client):
        await _call({"query": "x"}, ctx)
    call_kwargs = client.beta.messages.create.call_args[1]
    tools = call_kwargs["tools"]
    assert "allowed_domains" not in tools[0]
    assert "blocked_domains" not in tools[0]
