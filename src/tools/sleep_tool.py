import asyncio

from src.tool import Tool, ToolResult, build_tool

_SCHEMA = {
    "type": "object",
    "properties": {
        "seconds": {
            "type": "number",
            "description": "Number of seconds to sleep (max 3600).",
        },
    },
    "required": ["seconds"],
}


async def _call(args: dict, ctx) -> ToolResult:
    seconds = min(float(args["seconds"]), 3600.0)
    await asyncio.sleep(seconds)
    return ToolResult(
        content=[
            {"type": "text", "text": f"Slept for {seconds}s."}
        ]
    )


TOOL = build_tool(
    Tool(
        name="Sleep",
        description="Wait for a specified number of seconds.",
        input_schema=_SCHEMA,
        call=_call,
        is_read_only=lambda _: True,
        search_hint="sleep wait delay pause",
    )
)
