import pytest

from src.tools.brief_tool import _call


async def test_brief_short_format(ctx):
    result = await _call({}, ctx)
    text = result.content[0]["text"]
    assert "Messages: 2" in text
    assert "User: 1" in text
    assert "Assistant: 1" in text
    assert "Tools: 2" in text
    assert "Plan mode: False" in text


async def test_brief_full_format(ctx):
    result = await _call({"format": "full"}, ctx)
    text = result.content[0]["text"]
    assert "Model: claude-sonnet-4-6" in text
    assert "Max tokens: 8192" in text
    assert "Alpha" in text
    assert "Beta" in text


async def test_brief_default_is_short(ctx):
    result_default = await _call({}, ctx)
    result_short = await _call({"format": "short"}, ctx)
    assert result_default.content[0]["text"] == result_short.content[0]["text"]


async def test_brief_plan_mode(ctx):
    ctx.plan_mode = True
    result = await _call({}, ctx)
    assert "Plan mode: True" in result.content[0]["text"]


async def test_brief_no_error(ctx):
    result = await _call({}, ctx)
    assert not result.is_error
