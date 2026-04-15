import json
from pathlib import Path
from typing import Any

from src.tool import Tool, ToolResult, build_tool

_TODOS_PATH = Path(".omni-lilith/todos.json")

_SCHEMA = {
    "type": "object",
    "properties": {
        "todos": {
            "type": "array",
            "description": "Full list of todos to persist.",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "content": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["pending", "in_progress", "completed"],
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                    },
                },
                "required": ["id", "content", "status", "priority"],
            },
        },
    },
    "required": ["todos"],
}


async def _call(args: dict, ctx) -> ToolResult:
    todos: list[dict[str, Any]] = args["todos"]
    _TODOS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _TODOS_PATH.write_text(
        json.dumps(todos, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    pending = sum(1 for t in todos if t["status"] == "pending")
    in_prog = sum(1 for t in todos if t["status"] == "in_progress")
    done = sum(1 for t in todos if t["status"] == "completed")
    return ToolResult(
        content=[
            {
                "type": "text",
                "text": (
                    f"Todos saved: {len(todos)} total "
                    f"({pending} pending, {in_prog} in_progress, {done} done)"
                ),
            }
        ]
    )


TOOL = build_tool(
    Tool(
        name="TodoWrite",
        description=(
            "Persist the full todo list to disk. "
            "Always pass the complete list — this overwrites previous state."
        ),
        input_schema=_SCHEMA,
        call=_call,
        search_hint="todo list task write persist save",
    )
)
