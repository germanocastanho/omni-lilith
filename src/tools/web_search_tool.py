from __future__ import annotations

import os
from typing import Any

from src.tool import Tool, ToolResult, build_tool

_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "The search query (min 2 chars).",
        },
        "allowed_domains": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Only include results from these domains.",
        },
        "blocked_domains": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Exclude results from these domains.",
        },
    },
    "required": ["query"],
}


async def _call(args: dict, ctx) -> ToolResult:
    query = args["query"]
    allowed = args.get("allowed_domains", [])
    blocked = args.get("blocked_domains", [])

    try:
        result = await _run_web_search(query, allowed, blocked, ctx)
        return result
    except Exception as exc:
        return ToolResult(
            content=[{"type": "text", "text": f"Search error: {exc}"}],
            is_error=True,
        )


async def _run_web_search(
    query: str,
    allowed: list[str],
    blocked: list[str],
    ctx: Any,
) -> ToolResult:
    import anthropic

    client = anthropic.AsyncAnthropic(
        api_key=os.environ["ANTHROPIC_API_KEY"]
    )

    web_search_tool: dict[str, Any] = {
        "type": "web_search_20250305",
        "name": "web_search",
    }
    if allowed:
        web_search_tool["allowed_domains"] = allowed
    if blocked:
        web_search_tool["blocked_domains"] = blocked

    response = await client.beta.messages.create(
        model=ctx.model,
        max_tokens=4096,
        tools=[web_search_tool],  # type: ignore[list-item]
        messages=[
            {
                "role": "user",
                "content": (
                    f"Search the web for: {query}\n"
                    "Summarize the most relevant results."
                ),
            }
        ],
        betas=["web-search-2025-03-05"],
    )

    texts: list[str] = []
    for block in response.content:
        if hasattr(block, "text"):
            texts.append(block.text)

    text = "\n\n".join(texts) if texts else "(no results)"
    return ToolResult(content=[{"type": "text", "text": text}])


TOOL = build_tool(
    Tool(
        name="WebSearch",
        description=(
            "Search the web and return a synthesized summary of results."
        ),
        input_schema=_SCHEMA,
        call=_call,
        is_read_only=lambda _: True,
        search_hint="search web internet google bing query results",
    )
)
