from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, AsyncIterator

import anthropic

if TYPE_CHECKING:
    from src.context import ToolUseContext


def _client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(
        api_key=os.environ["ANTHROPIC_API_KEY"]
    )


async def stream_query(
    ctx: ToolUseContext,
    extra_headers: dict[str, str] | None = None,
) -> AsyncIterator[Any]:
    from src.tool import to_api_schema

    tools = [to_api_schema(t) for t in ctx.tools if t.is_enabled()]
    client = _client()

    kwargs: dict[str, Any] = {
        "model": ctx.model,
        "max_tokens": ctx.max_tokens,
        "messages": ctx.messages,
        "tools": tools,
        "stream": True,
    }
    if ctx.system:
        kwargs["system"] = ctx.system
    if extra_headers:
        kwargs["extra_headers"] = extra_headers

    async with client.messages.stream(**kwargs) as stream:
        async for event in stream:
            yield event
