import asyncio

import pytest

from src.context import ToolUseContext
from src.tool import Tool, build_tool


def _dummy_tool(name: str = "Dummy") -> Tool:
    async def _call(args, ctx):
        from src.tool import ToolResult
        return ToolResult(content=[{"type": "text", "text": "ok"}])

    return build_tool(Tool(
        name=name,
        description="dummy",
        input_schema={"type": "object", "properties": {}, "required": []},
        call=_call,
    ))


@pytest.fixture
def ctx():
    tools = [_dummy_tool("Alpha"), _dummy_tool("Beta")]
    return ToolUseContext(
        model="claude-sonnet-4-6",
        messages=[
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
        ],
        tools=tools,
    )
