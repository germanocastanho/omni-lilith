from unittest.mock import AsyncMock, patch

from src.tools.agent_tool import _call


def _patch_run_query(return_value="agent output"):
    return patch("src.query_engine.run_query", new=AsyncMock(return_value=return_value))


async def test_returns_result(ctx):
    with _patch_run_query("done"):
        result = await _call({"description": "d", "prompt": "do it"}, ctx)
    assert result.content[0]["text"] == "done"
    assert not result.is_error


async def test_fallback_when_none(ctx):
    with _patch_run_query(None):
        result = await _call({"description": "d", "prompt": "do it"}, ctx)
    assert "(agent returned no output)" in result.content[0]["text"]


async def test_forks_context_with_prompt(ctx):
    with _patch_run_query() as mock:
        await _call({"description": "d", "prompt": "specific task"}, ctx)
    sub_ctx = mock.call_args[0][0]
    assert sub_ctx.messages[0]["content"] == "specific task"
    assert sub_ctx.messages[0]["role"] == "user"


async def test_subagent_type_accepted(ctx):
    with _patch_run_query("ok"):
        result = await _call(
            {"description": "d", "prompt": "p", "subagent_type": "general-purpose"}, ctx
        )
    assert not result.is_error
