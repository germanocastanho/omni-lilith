from pathlib import Path

from src.tool import Tool, ToolResult, build_tool
from src.utils.format import truncate_lines

_SCHEMA = {
    "type": "object",
    "properties": {
        "file_path": {
            "type": "string",
            "description": "Absolute path to the file to read.",
        },
        "offset": {
            "type": "integer",
            "description": "Line number to start reading from (1-based).",
        },
        "limit": {
            "type": "integer",
            "description": "Number of lines to read.",
        },
    },
    "required": ["file_path"],
}


async def _call(args: dict, ctx) -> ToolResult:
    path = Path(args["file_path"])
    if not path.exists():
        return ToolResult(
            content=[{"type": "text", "text": f"File not found: {path}"}],
            is_error=True,
        )

    try:
        text = path.read_text(errors="replace")
    except Exception as exc:
        return ToolResult(
            content=[{"type": "text", "text": str(exc)}],
            is_error=True,
        )

    lines = text.splitlines(keepends=True)
    offset = max(0, int(args.get("offset", 1)) - 1)
    limit = args.get("limit")

    if limit is not None:
        lines = lines[offset : offset + int(limit)]
    else:
        lines = lines[offset:]

    numbered = "\n".join(
        f"{offset + i + 1}\t{line.rstrip()}"
        for i, line in enumerate(lines)
    )
    numbered = truncate_lines(numbered, 2000)

    return ToolResult(
        content=[{"type": "text", "text": numbered}],
    )


TOOL = build_tool(
    Tool(
        name="Read",
        description=(
            "Read a file from the filesystem. Returns content with "
            "line numbers. Use offset/limit for large files."
        ),
        input_schema=_SCHEMA,
        call=_call,
        is_read_only=lambda _: True,
        search_hint="read file cat head tail view contents",
    )
)
