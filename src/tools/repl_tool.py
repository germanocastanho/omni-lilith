import asyncio
import sys
from io import StringIO

from src.tool import Tool, ToolResult, build_tool
from src.utils.format import truncate

_SCHEMA = {
    "type": "object",
    "properties": {
        "code": {
            "type": "string",
            "description": "Python code to execute in the REPL.",
        },
    },
    "required": ["code"],
}

_repl_namespace: dict = {}


async def _call(args: dict, ctx) -> ToolResult:
    code = args["code"]
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    captured_out = StringIO()
    captured_err = StringIO()

    try:
        sys.stdout = captured_out
        sys.stderr = captured_err
        loop = asyncio.get_event_loop()

        def _exec():
            try:
                exec(compile(code, "<repl>", "exec"), _repl_namespace)
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)

        await loop.run_in_executor(None, _exec)
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    out = captured_out.getvalue()
    err = captured_err.getvalue()

    parts = []
    if out:
        parts.append(truncate(out, 20_000))
    if err:
        parts.append(f"<stderr>\n{truncate(err, 5_000)}\n</stderr>")

    text = "\n".join(parts) if parts else "(no output)"
    return ToolResult(
        content=[{"type": "text", "text": text}],
        is_error=bool(err and not out),
    )


TOOL = build_tool(
    Tool(
        name="REPL",
        description=(
            "Execute Python code in a persistent REPL namespace. "
            "Variables persist across calls within the same session."
        ),
        input_schema=_SCHEMA,
        call=_call,
        search_hint="python repl execute code run eval",
    )
)
