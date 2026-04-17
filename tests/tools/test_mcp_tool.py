import json
from unittest.mock import AsyncMock, patch

import pytest

import src.tools.mcp_tool as mcp_mod
from src.tools.mcp_tool import _call


def _patch_config(data: dict):
    return patch.object(mcp_mod, "_load_config", return_value=data)


def _patch_call_mcp(return_value="tool output"):
    return patch.object(mcp_mod, "_call_mcp", new=AsyncMock(return_value=return_value))


async def test_no_config_returns_error(ctx):
    with _patch_config({}):
        result = await _call({"server_name": "x", "tool_name": "y"}, ctx)
    assert result.is_error
    assert "No MCP servers configured" in result.content[0]["text"]


async def test_unknown_server_returns_error(ctx):
    with _patch_config({"known": {"command": "python3"}}):
        result = await _call({"server_name": "unknown", "tool_name": "y"}, ctx)
    assert result.is_error
    assert "unknown" in result.content[0]["text"]
    assert "known" in result.content[0]["text"]


async def test_successful_call(ctx):
    server_def = {"command": "python3", "args": []}
    with _patch_config({"myserver": server_def}), _patch_call_mcp("42"):
        result = await _call({"server_name": "myserver", "tool_name": "add"}, ctx)
    assert result.content[0]["text"] == "42"
    assert not result.is_error


async def test_mcp_exception_returns_error(ctx):
    server_def = {"command": "python3"}
    with _patch_config({"s": server_def}), \
         patch.object(mcp_mod, "_call_mcp", new=AsyncMock(side_effect=Exception("timeout"))):
        result = await _call({"server_name": "s", "tool_name": "t"}, ctx)
    assert result.is_error
    assert "MCP error" in result.content[0]["text"]


async def test_arguments_default_to_empty_dict(ctx):
    server_def = {"command": "python3"}
    with _patch_config({"s": server_def}), _patch_call_mcp() as mock:
        await _call({"server_name": "s", "tool_name": "t"}, ctx)
    mock.assert_awaited_once_with(server_def, "t", {})


async def test_explicit_arguments_forwarded(ctx):
    server_def = {"command": "python3"}
    args_in = {"key": "value"}
    with _patch_config({"s": server_def}), _patch_call_mcp() as mock:
        await _call({"server_name": "s", "tool_name": "t", "arguments": args_in}, ctx)
    mock.assert_awaited_once_with(server_def, "t", args_in)
