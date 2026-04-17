from unittest.mock import AsyncMock, patch

import pytest

import src.tools.bash_tool as bash_mod
from src.tools.bash_tool import _call
from src.utils.shell import ExecResult


def _exec(stdout="", stderr="", exit_code=0):
    mock = AsyncMock(return_value=ExecResult(stdout=stdout, stderr=stderr, exit_code=exit_code))
    return patch.object(bash_mod, "exec_cmd", mock)


async def test_bash_returns_stdout(ctx):
    with _exec(stdout="hello\n"):
        result = await _call({"command": "echo hello"}, ctx)
    assert "hello" in result.content[0]["text"]
    assert not result.is_error


async def test_bash_includes_stderr(ctx):
    with _exec(stderr="some warning\n"):
        result = await _call({"command": "cmd"}, ctx)
    assert "<stderr>" in result.content[0]["text"]
    assert "some warning" in result.content[0]["text"]


async def test_bash_nonzero_exit_is_error(ctx):
    with _exec(exit_code=1):
        result = await _call({"command": "false"}, ctx)
    assert result.is_error
    assert "<exit_code>1</exit_code>" in result.content[0]["text"]


async def test_bash_no_output(ctx):
    with _exec():
        result = await _call({"command": "true"}, ctx)
    assert result.content[0]["text"] == "(no output)"
    assert not result.is_error


async def test_bash_caps_timeout_at_600(ctx):
    with _exec() as mock:
        await _call({"command": "sleep 1", "timeout": 9999}, ctx)
    _, kwargs = mock.call_args
    assert kwargs["timeout"] == 600.0


async def test_bash_default_timeout_is_120(ctx):
    with _exec() as mock:
        await _call({"command": "true"}, ctx)
    _, kwargs = mock.call_args
    assert kwargs["timeout"] == 120.0


async def test_bash_exit_code_zero_not_shown(ctx):
    with _exec(stdout="ok", exit_code=0):
        result = await _call({"command": "true"}, ctx)
    assert "<exit_code>" not in result.content[0]["text"]
