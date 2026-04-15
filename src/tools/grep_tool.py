from src.tool import Tool, ToolResult, build_tool
from src.utils.format import truncate
from src.utils.shell import exec_cmd

_SCHEMA = {
    "type": "object",
    "properties": {
        "pattern": {
            "type": "string",
            "description": "Regular expression pattern to search for.",
        },
        "path": {
            "type": "string",
            "description": "File or directory to search in.",
        },
        "glob": {
            "type": "string",
            "description": "Glob pattern to filter files, e.g. '*.py'.",
        },
        "output_mode": {
            "type": "string",
            "enum": ["content", "files_with_matches", "count"],
            "description": (
                "content: show matching lines; "
                "files_with_matches: show file paths only; "
                "count: show match counts."
            ),
        },
        "-i": {
            "type": "boolean",
            "description": "Case-insensitive search.",
        },
        "context": {
            "type": "integer",
            "description": "Lines of context around each match.",
        },
        "head_limit": {
            "type": "integer",
            "description": "Limit output to first N results.",
        },
    },
    "required": ["pattern"],
}


async def _call(args: dict, ctx) -> ToolResult:
    pattern = args["pattern"]
    path = args.get("path", ".")
    glob = args.get("glob", "")
    output_mode = args.get("output_mode", "content")
    case_insensitive = args.get("-i", False)
    context = args.get("context")
    head_limit = args.get("head_limit", 250)

    flags = "-n --color=never"
    if case_insensitive:
        flags += " -i"
    if output_mode == "files_with_matches":
        flags += " -l"
    elif output_mode == "count":
        flags += " -c"
    if context:
        flags += f" -C {int(context)}"
    if glob:
        flags += f" --include='{glob}'"

    cmd = f"grep -r {flags} -- {_quote(pattern)} {_quote(path)}"
    result = await exec_cmd(cmd, timeout=30)

    output = result.stdout or result.stderr or "(no matches)"
    lines = output.splitlines()
    if head_limit and len(lines) > head_limit:
        lines = lines[:head_limit]
        lines.append(f"... [limited to {head_limit} lines]")

    text = truncate("\n".join(lines), 80_000)
    return ToolResult(content=[{"type": "text", "text": text}])


def _quote(s: str) -> str:
    return "'" + s.replace("'", "'\\''") + "'"


TOOL = build_tool(
    Tool(
        name="Grep",
        description=(
            "Search file contents using grep (regex). "
            "Supports output_mode: content, files_with_matches, count. "
            "Use for finding code patterns, strings, symbols."
        ),
        input_schema=_SCHEMA,
        call=_call,
        is_read_only=lambda _: True,
        search_hint="search grep regex find pattern content files",
    )
)
