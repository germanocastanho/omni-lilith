from pathlib import Path

from src.tool import Tool, ToolResult, build_tool

_SCHEMA = {
    "type": "object",
    "properties": {
        "file_path": {
            "type": "string",
            "description": "Absolute path to the file to write.",
        },
        "content": {
            "type": "string",
            "description": "Content to write to the file.",
        },
    },
    "required": ["file_path", "content"],
}


async def _call(args: dict, ctx) -> ToolResult:
    path = Path(args["file_path"])
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(args["content"], encoding="utf-8")
        return ToolResult(
            content=[
                {"type": "text", "text": f"Wrote {path}"}
            ]
        )
    except Exception as exc:
        return ToolResult(
            content=[{"type": "text", "text": str(exc)}],
            is_error=True,
        )


TOOL = build_tool(
    Tool(
        name="Write",
        description=(
            "Write content to a file, creating it if it doesn't exist. "
            "Overwrites existing content. Prefer Edit for partial changes."
        ),
        input_schema=_SCHEMA,
        call=_call,
        search_hint="write create file save overwrite",
    )
)
