from src.tool import Tool, ToolResult, build_tool

_SCHEMA = {
    "type": "object",
    "properties": {
        "format": {
            "type": "string",
            "enum": ["short", "full"],
            "description": "Output format (default: short).",
        },
    },
    "required": [],
}


async def _call(args: dict, ctx) -> ToolResult:
    fmt = args.get("format", "short")
    n = len(ctx.messages)
    user_msgs = sum(1 for m in ctx.messages if m.get("role") == "user")
    assistant_msgs = sum(
        1 for m in ctx.messages if m.get("role") == "assistant"
    )
    tools_enabled = [t.name for t in ctx.tools if t.is_enabled()]
    plan_mode = getattr(ctx, "plan_mode", False)

    if fmt == "short":
        text = (
            f"Messages: {n} | User: {user_msgs} | "
            f"Assistant: {assistant_msgs} | "
            f"Tools: {len(tools_enabled)} | "
            f"Plan mode: {plan_mode}"
        )
    else:
        text = (
            f"Model: {ctx.model}\n"
            f"Messages: {n} (user={user_msgs}, assistant={assistant_msgs})\n"
            f"Plan mode: {plan_mode}\n"
            f"Max tokens: {ctx.max_tokens}\n"
            f"Tools enabled ({len(tools_enabled)}):\n"
            + "\n".join(f"  - {t}" for t in tools_enabled)
        )

    return ToolResult(content=[{"type": "text", "text": text}])


TOOL = build_tool(
    Tool(
        name="Brief",
        description=(
            "Return a brief summary of the current session context: "
            "message count, model, tools enabled, plan mode."
        ),
        input_schema=_SCHEMA,
        call=_call,
        is_read_only=lambda _: True,
        search_hint="context summary session info status brief",
    )
)
