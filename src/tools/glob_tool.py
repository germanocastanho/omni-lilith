from pathlib import Path

from src.tool import Tool, ToolResult, build_tool

_SCHEMA = {
    "type": "object",
    "properties": {
        "pattern": {
            "type": "string",
            "description": (
                "Glob pattern to match files, e.g. '**/*.py' or 'src/**/*.ts'."
            ),
        },
        "path": {
            "type": "string",
            "description": (
                "Directory to search in. Defaults to current directory."
            ),
        },
    },
    "required": ["pattern"],
}

_MAX_RESULTS = 1000


async def _call(args: dict, ctx) -> ToolResult:
    pattern = args["pattern"]
    base = Path(args.get("path", ".")).resolve()

    if not base.exists():
        return ToolResult(
            content=[
                {"type": "text", "text": f"Directory not found: {base}"}
            ],
            is_error=True,
        )

    try:
        matches = sorted(base.glob(pattern))
    except Exception as exc:
        return ToolResult(
            content=[{"type": "text", "text": str(exc)}],
            is_error=True,
        )

    truncated = matches[:_MAX_RESULTS]
    lines = [str(p) for p in truncated]
    if len(matches) > _MAX_RESULTS:
        lines.append(
            f"... [{len(matches) - _MAX_RESULTS} more results omitted]"
        )

    text = "\n".join(lines) if lines else "(no matches)"
    return ToolResult(content=[{"type": "text", "text": text}])


TOOL = build_tool(
    Tool(
        name="Glob",
        description=(
            "Find files matching a glob pattern. Returns sorted file paths. "
            "Use for discovering files by name pattern."
        ),
        input_schema=_SCHEMA,
        call=_call,
        is_read_only=lambda _: True,
        search_hint="find files glob pattern match list directory",
    )
)
