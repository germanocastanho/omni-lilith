from src.tool import Tool, ToolResult, build_tool
from src.utils.format import truncate
from src.utils.shell import exec_cmd

_SCHEMA = {
    "type": "object",
    "properties": {
        "command": {
            "type": "string",
            "description": "The PowerShell command to execute.",
        },
        "timeout": {
            "type": "number",
            "description": "Timeout in seconds (default 120).",
        },
    },
    "required": ["command"],
}


async def _call(args: dict, ctx) -> ToolResult:
    command = args["command"]
    timeout = min(float(args.get("timeout", 120)), 600.0)
    escaped = command.replace("'", "\\'")
    cmd = f"pwsh -Command '{escaped}'"
    result = await exec_cmd(cmd, timeout=timeout)

    parts = []
    if result.stdout:
        parts.append(truncate(result.stdout, 50_000))
    if result.stderr:
        parts.append(
            f"<stderr>\n{truncate(result.stderr, 10_000)}\n</stderr>"
        )
    if result.exit_code != 0:
        parts.append(f"<exit_code>{result.exit_code}</exit_code>")

    text = "\n".join(parts) if parts else "(no output)"
    return ToolResult(
        content=[{"type": "text", "text": text}],
        is_error=result.exit_code != 0,
    )


TOOL = build_tool(
    Tool(
        name="PowerShell",
        description=(
            "Execute a PowerShell command using pwsh. "
            "Requires PowerShell Core installed on the system."
        ),
        input_schema=_SCHEMA,
        call=_call,
        search_hint="powershell pwsh windows command shell",
    )
)
