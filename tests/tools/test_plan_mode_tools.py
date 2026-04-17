from unittest.mock import patch

from src.tools.plan_mode_tools import _enter, _exit


async def test_enter_sets_plan_mode(ctx):
    ctx.plan_mode = False
    with patch("rich.console.Console"):
        result = await _enter({}, ctx)
    assert ctx.plan_mode is True
    assert "Entered" in result.content[0]["text"]


async def test_enter_with_plan_text(ctx):
    with patch("rich.console.Console"):
        result = await _enter({"plan": "Step 1: do X"}, ctx)
    assert not result.is_error


async def test_exit_clears_plan_mode(ctx):
    ctx.plan_mode = True
    result = await _exit({}, ctx)
    assert ctx.plan_mode is False
    assert "Exited" in result.content[0]["text"]
