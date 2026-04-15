from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field

from src.tool import Tool, ToolResult, build_tool

_tasks: dict[str, "_TaskEntry"] = {}


@dataclass
class _TaskEntry:
    task_id: str
    subject: str
    description: str
    status: str = "pending"
    output: list[str] = field(default_factory=list)
    asyncio_task: asyncio.Task | None = None


def _get(task_id: str) -> _TaskEntry | None:
    return _tasks.get(task_id)


# --- TaskCreate ---

_CREATE_SCHEMA = {
    "type": "object",
    "properties": {
        "subject": {
            "type": "string",
            "description": "Short title for the task.",
        },
        "description": {
            "type": "string",
            "description": "What needs to be done.",
        },
    },
    "required": ["subject", "description"],
}


async def _create(args: dict, ctx) -> ToolResult:
    task_id = str(uuid.uuid4())[:8]
    entry = _TaskEntry(
        task_id=task_id,
        subject=args["subject"],
        description=args["description"],
    )
    _tasks[task_id] = entry
    return ToolResult(
        content=[
            {
                "type": "text",
                "text": f"Task #{task_id} created: {args['subject']}",
            }
        ]
    )


TASK_CREATE = build_tool(
    Tool(
        name="TaskCreate",
        description="Create a new task to track progress.",
        input_schema=_CREATE_SCHEMA,
        call=_create,
        search_hint="create task todo progress track",
    )
)

# --- TaskList ---

_LIST_SCHEMA = {"type": "object", "properties": {}, "required": []}


async def _list(args: dict, ctx) -> ToolResult:
    if not _tasks:
        return ToolResult(
            content=[{"type": "text", "text": "No tasks."}]
        )
    lines = []
    for t in _tasks.values():
        lines.append(f"#{t.task_id} [{t.status}] {t.subject}")
    return ToolResult(
        content=[{"type": "text", "text": "\n".join(lines)}]
    )


TASK_LIST = build_tool(
    Tool(
        name="TaskList",
        description="List all current tasks and their status.",
        input_schema=_LIST_SCHEMA,
        call=_list,
        is_read_only=lambda _: True,
        search_hint="list tasks todos status pending",
    )
)

# --- TaskGet ---

_GET_SCHEMA = {
    "type": "object",
    "properties": {
        "taskId": {"type": "string", "description": "Task ID."},
    },
    "required": ["taskId"],
}


async def _get(args: dict, ctx) -> ToolResult:
    entry = _get(args["taskId"])
    if entry is None:
        return ToolResult(
            content=[
                {"type": "text", "text": f"Task {args['taskId']} not found."}
            ],
            is_error=True,
        )
    text = (
        f"#{entry.task_id} [{entry.status}]\n"
        f"Subject: {entry.subject}\n"
        f"Description: {entry.description}\n"
        f"Output lines: {len(entry.output)}"
    )
    return ToolResult(content=[{"type": "text", "text": text}])


TASK_GET = build_tool(
    Tool(
        name="TaskGet",
        description="Get details of a specific task by ID.",
        input_schema=_GET_SCHEMA,
        call=_get,
        is_read_only=lambda _: True,
        search_hint="get task details info status",
    )
)

# --- TaskUpdate ---

_UPDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "taskId": {"type": "string", "description": "Task ID."},
        "status": {
            "type": "string",
            "enum": ["pending", "in_progress", "completed", "deleted"],
        },
        "subject": {"type": "string"},
        "description": {"type": "string"},
    },
    "required": ["taskId"],
}


async def _update(args: dict, ctx) -> ToolResult:
    task_id = args["taskId"]
    entry = _tasks.get(task_id)
    if entry is None:
        return ToolResult(
            content=[
                {"type": "text", "text": f"Task {task_id} not found."}
            ],
            is_error=True,
        )
    if "status" in args:
        if args["status"] == "deleted":
            del _tasks[task_id]
            return ToolResult(
                content=[{"type": "text", "text": f"Task {task_id} deleted."}]
            )
        entry.status = args["status"]
    if "subject" in args:
        entry.subject = args["subject"]
    if "description" in args:
        entry.description = args["description"]
    return ToolResult(
        content=[{"type": "text", "text": f"Task {task_id} updated."}]
    )


TASK_UPDATE = build_tool(
    Tool(
        name="TaskUpdate",
        description="Update a task's status, subject, or description.",
        input_schema=_UPDATE_SCHEMA,
        call=_update,
        search_hint="update task status complete progress",
    )
)

# --- TaskStop ---

_STOP_SCHEMA = {
    "type": "object",
    "properties": {
        "taskId": {"type": "string", "description": "Task ID to stop."},
    },
    "required": ["taskId"],
}


async def _stop(args: dict, ctx) -> ToolResult:
    task_id = args["taskId"]
    entry = _tasks.get(task_id)
    if entry is None:
        return ToolResult(
            content=[
                {"type": "text", "text": f"Task {task_id} not found."}
            ],
            is_error=True,
        )
    if entry.asyncio_task and not entry.asyncio_task.done():
        entry.asyncio_task.cancel()
    entry.status = "stopped"
    return ToolResult(
        content=[{"type": "text", "text": f"Task {task_id} stopped."}]
    )


TASK_STOP = build_tool(
    Tool(
        name="TaskStop",
        description="Stop a running task.",
        input_schema=_STOP_SCHEMA,
        call=_stop,
        search_hint="stop cancel kill task",
    )
)

# --- TaskOutput ---

_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "taskId": {"type": "string", "description": "Task ID."},
        "lines": {
            "type": "integer",
            "description": "Last N lines to return (default 50).",
        },
    },
    "required": ["taskId"],
}


async def _output(args: dict, ctx) -> ToolResult:
    task_id = args["taskId"]
    entry = _tasks.get(task_id)
    if entry is None:
        return ToolResult(
            content=[
                {"type": "text", "text": f"Task {task_id} not found."}
            ],
            is_error=True,
        )
    lines = int(args.get("lines", 50))
    tail = entry.output[-lines:] if entry.output else []
    text = "\n".join(tail) if tail else "(no output yet)"
    return ToolResult(content=[{"type": "text", "text": text}])


TASK_OUTPUT = build_tool(
    Tool(
        name="TaskOutput",
        description="Get the output/logs of a task.",
        input_schema=_OUTPUT_SCHEMA,
        call=_output,
        is_read_only=lambda _: True,
        search_hint="task output logs result stdout",
    )
)
