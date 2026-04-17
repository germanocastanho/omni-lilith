from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import src.tools.worktree_tools as wt_mod
from src.tools.worktree_tools import _enter, _exit


def _patch_exec(stdout="", stderr="", exit_code=0):
    result = SimpleNamespace(stdout=stdout, stderr=stderr, exit_code=exit_code)
    return patch.object(wt_mod, "exec_cmd", new=AsyncMock(return_value=result))


def _patch_exec_seq(results):
    it = iter(results)
    return patch.object(
        wt_mod, "exec_cmd", new=AsyncMock(side_effect=lambda *a, **kw: next(it))
    )


async def test_enter_success(ctx):
    ok = SimpleNamespace(stdout="", stderr="", exit_code=0)
    with _patch_exec_seq([ok]):
        result = await _enter({"branch": "feat/x"}, ctx)
    assert not result.is_error
    assert "feat/x" in result.content[0]["text"]


async def test_enter_uses_default_path(ctx):
    ok = SimpleNamespace(stdout="", stderr="", exit_code=0)
    with _patch_exec_seq([ok]) as mock:
        await _enter({"branch": "my-branch"}, ctx)
    cmd = mock.call_args[0][0]
    assert "/tmp/worktree-my-branch" in cmd


async def test_enter_custom_path(ctx):
    ok = SimpleNamespace(stdout="", stderr="", exit_code=0)
    with _patch_exec_seq([ok]) as mock:
        await _enter({"branch": "b", "path": "/tmp/custom"}, ctx)
    cmd = mock.call_args[0][0]
    assert "/tmp/custom" in cmd


async def test_enter_falls_back_to_new_branch(ctx):
    fail = SimpleNamespace(stdout="", stderr="no such branch", exit_code=1)
    ok = SimpleNamespace(stdout="", stderr="", exit_code=0)
    with _patch_exec_seq([fail, ok]):
        result = await _enter({"branch": "new-feat"}, ctx)
    assert not result.is_error


async def test_enter_both_fail_returns_error(ctx):
    fail = SimpleNamespace(stdout="", stderr="err", exit_code=1)
    with _patch_exec_seq([fail, fail]):
        result = await _enter({"branch": "bad"}, ctx)
    assert result.is_error


async def test_exit_success(ctx):
    with _patch_exec():
        result = await _exit({"path": "/tmp/worktree-feat"}, ctx)
    assert not result.is_error
    assert "removed" in result.content[0]["text"]


async def test_exit_error(ctx):
    with _patch_exec(stderr="not a worktree", exit_code=128):
        result = await _exit({"path": "/tmp/bad"}, ctx)
    assert result.is_error
    assert "not a worktree" in result.content[0]["text"]
