from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.text import Text

from src.context import ToolUseContext
from src.permissions import check_tool_permission
from src.tool import Tool, ToolResult

_console = Console()

MAX_ITERATIONS = 50


async def run_query(ctx: ToolUseContext) -> str:
    from src.services.api import stream_query

    iterations = 0
    final_text = ""

    while iterations < MAX_ITERATIONS:
        if ctx.is_aborted():
            break

        iterations += 1
        response_text = ""
        tool_uses: list[dict[str, Any]] = []
        stop_reason = ""

        current_block: dict[str, Any] | None = None
        input_json_buf = ""

        if ctx.verbose:
            _console.print(
                f"[dim]iteration {iterations}, "
                f"messages: {len(ctx.messages)}[/]"
            )

        with Live(Text(""), console=_console, refresh_per_second=20) as live:
            async for event in stream_query(ctx):
                if ctx.is_aborted():
                    break

                etype = type(event).__name__

                if etype == "RawContentBlockStartEvent":
                    block = event.content_block
                    btype = getattr(block, "type", "")
                    if btype == "text":
                        current_block = {"type": "text", "text": ""}
                    elif btype == "tool_use":
                        current_block = {
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": {},
                        }
                        input_json_buf = ""

                elif etype == "RawContentBlockDeltaEvent":
                    delta = event.delta
                    dtype = getattr(delta, "type", "")
                    if dtype == "text_delta" and current_block:
                        chunk = delta.text
                        current_block["text"] = (
                            current_block.get("text", "") + chunk
                        )
                        response_text += chunk
                        live.update(Markdown(response_text))
                    elif dtype == "input_json_delta" and current_block:
                        input_json_buf += delta.partial_json

                elif etype == "RawContentBlockStopEvent":
                    if current_block:
                        if current_block["type"] == "tool_use":
                            try:
                                current_block["input"] = json.loads(
                                    input_json_buf or "{}"
                                )
                            except json.JSONDecodeError:
                                current_block["input"] = {}
                            tool_uses.append(current_block)
                        current_block = None
                        input_json_buf = ""

                elif etype == "RawMessageDeltaEvent":
                    stop_reason = getattr(
                        event.delta, "stop_reason", ""
                    ) or ""

        if response_text:
            final_text = response_text
            ctx.messages.append(
                {"role": "assistant", "content": response_text}
            )

        if stop_reason == "end_turn" or not tool_uses:
            break

        if tool_uses:
            assistant_content: list[dict[str, Any]] = []
            if response_text:
                assistant_content.append(
                    {"type": "text", "text": response_text}
                )
            for tu in tool_uses:
                assistant_content.append(
                    {
                        "type": "tool_use",
                        "id": tu["id"],
                        "name": tu["name"],
                        "input": tu["input"],
                    }
                )
            if assistant_content:
                ctx.messages[-1] = {
                    "role": "assistant",
                    "content": assistant_content,
                }
            elif not response_text:
                ctx.messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_content,
                    }
                )

            tool_results = await _dispatch_tools(tool_uses, ctx)
            ctx.messages.append(
                {"role": "user", "content": tool_results}
            )

    return final_text


async def _dispatch_tools(
    tool_uses: list[dict[str, Any]],
    ctx: ToolUseContext,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    for tu in tool_uses:
        tool = _find_tool(ctx.tools, tu["name"])
        if tool is None:
            results.append(
                _tool_error(
                    tu["id"],
                    f"Unknown tool: {tu['name']}",
                )
            )
            continue

        args = tu["input"]
        perm = await check_tool_permission(tool, args, ctx)
        if perm.behavior == "deny":
            results.append(
                _tool_error(
                    tu["id"],
                    f"Permission denied: {perm.message}",
                )
            )
            continue

        effective_args = perm.updated_input or args

        if ctx.verbose:
            _console.print(
                f"[bold green]→[/] [cyan]{tool.name}[/] "
                f"[dim]{_summarize_args(effective_args)}[/]"
            )

        try:
            result: ToolResult = await tool.call(effective_args, ctx)
        except Exception as exc:  # noqa: BLE001
            result = ToolResult(
                content=[
                    {"type": "text", "text": f"Error: {exc}"}
                ],
                is_error=True,
            )

        if ctx.verbose:
            status = "[red]error[/]" if result.is_error else "[green]ok[/]"
            _console.print(f"  {status}")

        results.append(
            {
                "type": "tool_result",
                "tool_use_id": tu["id"],
                "content": result.content,
                "is_error": result.is_error,
            }
        )

    return results


def _find_tool(tools: list[Tool], name: str) -> Tool | None:
    for t in tools:
        if t.name == name or name in (t.aliases or []):
            return t
    return None


def _tool_error(tool_use_id: str, message: str) -> dict[str, Any]:
    return {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": [{"type": "text", "text": message}],
        "is_error": True,
    }


def _summarize_args(args: dict[str, Any], max_len: int = 80) -> str:
    s = json.dumps(args, ensure_ascii=False)
    if len(s) > max_len:
        return s[:max_len] + "..."
    return s
