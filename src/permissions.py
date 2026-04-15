from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.prompt import Confirm

from src.tool import PermissionResult, Tool

_console = Console()

_ALWAYS_ALLOW: set[str] = {
    "Read",
    "Glob",
    "Grep",
    "WebSearch",
    "WebFetch",
    "TodoWrite",
    "ToolSearch",
    "Sleep",
    "Brief",
}

_ALWAYS_ASK: set[str] = {
    "Bash",
    "Write",
    "Edit",
    "NotebookEdit",
    "PowerShell",
}


async def check_tool_permission(
    tool: Tool,
    args: dict[str, Any],
    ctx: Any,
) -> PermissionResult:
    if not tool.is_enabled():
        return PermissionResult(
            behavior="deny", message=f"Tool {tool.name} is disabled."
        )

    if tool.check_permissions:
        result = await tool.check_permissions(args, ctx)
        if result.behavior != "allow":
            return result

    if tool.name in _ALWAYS_ALLOW:
        return PermissionResult(behavior="allow", updated_input=args)

    if tool.name in _ALWAYS_ASK:
        _console.print(
            f"\n[bold yellow]Permission:[/] [cyan]{tool.name}[/] "
            f"wants to run with args: [dim]{_summarize(args)}[/]"
        )
        approved = Confirm.ask("Allow?", default=True)
        if not approved:
            return PermissionResult(
                behavior="deny", message="User denied permission."
            )

    return PermissionResult(behavior="allow", updated_input=args)


def _summarize(args: dict[str, Any], max_len: int = 120) -> str:
    import json

    s = json.dumps(args, ensure_ascii=False)
    if len(s) > max_len:
        return s[:max_len] + "..."
    return s
