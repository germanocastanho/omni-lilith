from src.tool import Tool, ToolResult, build_tool

_SCHEMA = {
    "type": "object",
    "properties": {
        "content": {
            "type": "string",
            "description": "Synthetic content to inject into the conversation.",
        },
        "role": {
            "type": "string",
            "enum": ["user", "assistant"],
            "description": "Role for the injected message (default: user).",
        },
    },
    "required": ["content"],
}


async def _call(args: dict, ctx) -> ToolResult:
    content = args["content"]
    role = args.get("role", "user")
    ctx.messages.append({"role": role, "content": content})
    return ToolResult(
        content=[
            {
                "type": "text",
                "text": f"Injected {role} message into conversation.",
            }
        ]
    )


TOOL = build_tool(
    Tool(
        name="SyntheticOutput",
        description=(
            "Inject a synthetic message into the conversation history. "
            "Useful for testing or seeding context."
        ),
        input_schema=_SCHEMA,
        call=_call,
        search_hint="inject message synthetic context history",
    )
)
