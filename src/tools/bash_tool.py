from src.tool import Tool, ToolResult, build_tool
from src.utils.format import truncate
from src.utils.shell import exec_cmd

_SCHEMA = {
    "type": "object",
    "properties": {
        "command": {
            "type": "string",
            "description": "The bash command to execute.",
        },
        "timeout": {
            "type": "number",
            "description": (
                "Timeout in seconds (default 120, max 600)."
            ),
        },
        "description": {
            "type": "string",
            "description": "Short description of what the command does.",
        },
    },
    "required": ["command"],
}


async def _call(args: dict, ctx) -> ToolResult:
    command = args["command"]
    timeout = min(float(args.get("timeout", 120)), 600.0)
    result = await exec_cmd(command, timeout=timeout)

    parts: list[str] = []
    if result.stdout:
        parts.append(truncate(result.stdout, 50_000))
    if result.stderr:
        parts.append(f"<stderr>\n{truncate(result.stderr, 10_000)}\n</stderr>")
    if result.exit_code != 0:
        parts.append(f"<exit_code>{result.exit_code}</exit_code>")

    text = "\n".join(parts) if parts else "(no output)"
    return ToolResult(
        content=[{"type": "text", "text": text}],
        is_error=result.exit_code != 0,
    )


TOOL = build_tool(
    Tool(
        name="Bash",
        description=(
            "Execute a bash command. Use for shell operations, "
            "running scripts, git commands, and system tasks. "
            "Always prefer dedicated tools (Read, Edit, Glob, Grep) "
            "over bash for file operations."
        ),
        input_schema=_SCHEMA,
        call=_call,
        is_read_only=lambda args: False,
        search_hint="shell command execute terminal run script",
    )
)
