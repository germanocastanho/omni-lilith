from unittest.mock import AsyncMock, patch

import pytest

import src.tools.grep_tool as grep_mod
from src.tools.grep_tool import _call, _quote
from src.utils.shell import ExecResult


def _exec(stdout="", stderr="", exit_code=0):
    mock = AsyncMock(return_value=ExecResult(stdout=stdout, stderr=stderr, exit_code=exit_code))
    return patch.object(grep_mod, "exec_cmd", mock)


# --- _quote unit tests ---

def test_quote_simple():
    assert _quote("hello") == "'hello'"


def test_quote_with_single_quote():
    assert _quote("it's") == "'it'\\''s'"


# --- _call tests ---

async def test_grep_returns_matches(ctx):
    with _exec(stdout="file.py:1:hello world\n") as mock:
        result = await _call({"pattern": "hello"}, ctx)
    assert "hello world" in result.content[0]["text"]
    assert not result.is_error


async def test_grep_no_matches_uses_stderr(ctx):
    with _exec(stdout="", stderr="") as mock:
        result = await _call({"pattern": "xyz"}, ctx)
    assert result.content[0]["text"] == "(no matches)"


async def test_grep_case_insensitive_flag(ctx):
    with _exec() as mock:
        await _call({"pattern": "X", "-i": True}, ctx)
    cmd = mock.call_args[0][0]
    assert " -i" in cmd


async def test_grep_files_with_matches_mode(ctx):
    with _exec() as mock:
        await _call({"pattern": "X", "output_mode": "files_with_matches"}, ctx)
    cmd = mock.call_args[0][0]
    assert " -l" in cmd


async def test_grep_count_mode(ctx):
    with _exec() as mock:
        await _call({"pattern": "X", "output_mode": "count"}, ctx)
    cmd = mock.call_args[0][0]
    assert " -c" in cmd


async def test_grep_context_lines(ctx):
    with _exec() as mock:
        await _call({"pattern": "X", "context": 3}, ctx)
    cmd = mock.call_args[0][0]
    assert "-C 3" in cmd


async def test_grep_head_limit_truncates(ctx):
    lines = "\n".join(f"line{i}" for i in range(300))
    with _exec(stdout=lines):
        result = await _call({"pattern": "line", "head_limit": 10}, ctx)
    text = result.content[0]["text"]
    assert "limited to 10 lines" in text


async def test_grep_glob_filter(ctx):
    with _exec() as mock:
        await _call({"pattern": "X", "glob": "*.py"}, ctx)
    cmd = mock.call_args[0][0]
    assert "--include='*.py'" in cmd
