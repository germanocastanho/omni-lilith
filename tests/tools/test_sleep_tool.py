from unittest.mock import AsyncMock, patch

import pytest

from src.tools.sleep_tool import _call


async def test_sleep_caps_at_3600(ctx):
    with patch("src.tools.sleep_tool.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = await _call({"seconds": 9999}, ctx)
    mock_sleep.assert_awaited_once_with(3600.0)
    assert result.content[0]["text"] == "Slept for 3600.0s."


async def test_sleep_exact_value(ctx):
    with patch("src.tools.sleep_tool.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = await _call({"seconds": 0}, ctx)
    mock_sleep.assert_awaited_once_with(0.0)
    assert result.content[0]["text"] == "Slept for 0.0s."


async def test_sleep_returns_single_text_block(ctx):
    with patch("src.tools.sleep_tool.asyncio.sleep", new_callable=AsyncMock):
        result = await _call({"seconds": 1}, ctx)
    assert len(result.content) == 1
    assert result.content[0]["type"] == "text"
    assert not result.is_error
