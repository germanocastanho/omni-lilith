from __future__ import annotations

import uuid

from src.tool import Tool, ToolResult, build_tool

_SCHEMA = {
    "type": "object",
    "properties": {
        "description": {
            "type": "string",
            "description": "Short description of what the agent will do.",
        },
        "prompt": {
            "type": "string",
            "description": (
                "The full task prompt for the subagent. "
                "Must be self-contained with all context needed."
            ),
        },
        "subagent_type": {
            "type": "string",
            "description": (
                "Optional agent specialization type, e.g. 'general-purpose'."
            ),
        },
    },
    "required": ["description", "prompt"],
}


async def _call(args: dict, ctx) -> ToolResult:
    from src.query_engine import run_query

    prompt = args["prompt"]
    agent_id = str(uuid.uuid4())[:8]

    sub_ctx = ctx.fork(
        extra_messages=[{"role": "user", "content": prompt}]
    )
    sub_ctx.agent_id = agent_id
    sub_ctx.messages = [{"role": "user", "content": prompt}]

    result = await run_query(sub_ctx)
    return ToolResult(
        content=[{"type": "text", "text": result or "(agent returned no output)"}]
    )


TOOL = build_tool(
    Tool(
        name="Agent",
        description=(
            "Launch a subagent to handle a complex, multi-step task. "
            "The subagent runs with full access to all tools. "
            "Provide a self-contained prompt with all context needed."
        ),
        input_schema=_SCHEMA,
        call=_call,
        is_concurrency_safe=lambda _: True,
        search_hint="subagent delegate spawn parallel agent task",
    )
)
