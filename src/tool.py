from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Awaitable, Callable

if TYPE_CHECKING:
    from src.context import ToolUseContext

type ToolContent = list[dict[str, Any]]


@dataclass
class ToolResult:
    content: ToolContent
    is_error: bool = False


@dataclass
class PermissionResult:
    behavior: str  # "allow" | "deny" | "ask"
    message: str = ""
    updated_input: dict[str, Any] | None = None


CallFn = Callable[
    [dict[str, Any], "ToolUseContext"],
    Awaitable[ToolResult],
]

PermissionFn = Callable[
    [dict[str, Any], "ToolUseContext"],
    Awaitable[PermissionResult],
]


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict[str, Any]
    call: CallFn
    check_permissions: PermissionFn | None = None
    is_read_only: Callable[[dict[str, Any]], bool] | None = None
    is_enabled: Callable[[], bool] | None = None
    is_concurrency_safe: Callable[[dict[str, Any]], bool] | None = None
    search_hint: str = ""
    aliases: list[str] = field(default_factory=list)
    max_result_size_chars: int = 100_000


def _default_allow(
    args: dict[str, Any], _ctx: Any
) -> Awaitable[PermissionResult]:

    async def _allow() -> PermissionResult:
        return PermissionResult(behavior="allow", updated_input=args)

    return _allow()


def build_tool(tool: Tool) -> Tool:
    if tool.check_permissions is None:
        tool.check_permissions = _default_allow
    if tool.is_read_only is None:
        tool.is_read_only = lambda _: False
    if tool.is_enabled is None:
        tool.is_enabled = lambda: True
    if tool.is_concurrency_safe is None:
        tool.is_concurrency_safe = lambda _: False
    return tool


def to_api_schema(tool: Tool) -> dict[str, Any]:
    return {
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.input_schema,
    }
