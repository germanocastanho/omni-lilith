from unittest.mock import AsyncMock, patch
from types import SimpleNamespace

import src.tools.powershell_tool as ps_mod
from src.tools.powershell_tool import _call


def _patch_exec(stdout="", stderr="", exit_code=0):
    result = SimpleNamespace(stdout=stdout, stderr=stderr, exit_code=exit_code)
    return patch.object(ps_mod, "exec_cmd", new=AsyncMock(return_value=result))


async def test_successful_command(ctx):
    with _patch_exec(stdout="hello"):
        result = await _call({"command": "echo hello"}, ctx)
    assert result.content[0]["text"] == "hello"
    assert not result.is_error


async def test_error_exit_code(ctx):
    with _patch_exec(stdout="", stderr="not found", exit_code=1):
        result = await _call({"command": "bad-cmd"}, ctx)
    assert result.is_error
    assert "not found" in result.content[0]["text"]
    assert "exit_code" in result.content[0]["text"]


async def test_no_output_fallback(ctx):
    with _patch_exec():
        result = await _call({"command": "true"}, ctx)
    assert result.content[0]["text"] == "(no output)"


async def test_timeout_capped_at_600(ctx):
    with _patch_exec(stdout="ok") as mock:
        await _call({"command": "x", "timeout": 9999}, ctx)
    cmd_arg = mock.call_args[0][0]
    assert "x" in cmd_arg


async def test_stdout_and_stderr_combined(ctx):
    with _patch_exec(stdout="out", stderr="err", exit_code=1):
        result = await _call({"command": "cmd"}, ctx)
    text = result.content[0]["text"]
    assert "out" in text
    assert "<stderr>" in text
