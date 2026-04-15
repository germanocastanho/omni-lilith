import json
from pathlib import Path
from typing import Any

from src.tool import Tool, ToolResult, build_tool

_CRONS_PATH = Path(".omni-lilith/crons.json")

_CREATE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "Unique cron name."},
        "schedule": {
            "type": "string",
            "description": "Cron expression e.g. '0 9 * * 1-5'.",
        },
        "prompt": {
            "type": "string",
            "description": "Prompt to run on schedule.",
        },
    },
    "required": ["name", "schedule", "prompt"],
}

_DELETE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "Cron name to delete."},
    },
    "required": ["name"],
}

_LIST_SCHEMA = {"type": "object", "properties": {}, "required": []}


def _load() -> list[dict[str, Any]]:
    if _CRONS_PATH.exists():
        try:
            return json.loads(_CRONS_PATH.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save(crons: list[dict[str, Any]]) -> None:
    _CRONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CRONS_PATH.write_text(
        json.dumps(crons, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


async def _create(args: dict, ctx) -> ToolResult:
    crons = _load()
    if any(c["name"] == args["name"] for c in crons):
        return ToolResult(
            content=[
                {
                    "type": "text",
                    "text": (
                        f"Cron '{args['name']}' already exists. "
                        "Delete it first."
                    ),
                }
            ],
            is_error=True,
        )
    crons.append(
        {
            "name": args["name"],
            "schedule": args["schedule"],
            "prompt": args["prompt"],
        }
    )
    _save(crons)
    return ToolResult(
        content=[
            {
                "type": "text",
                "text": (
                    f"Cron '{args['name']}' created "
                    f"({args['schedule']})."
                ),
            }
        ]
    )


async def _delete(args: dict, ctx) -> ToolResult:
    crons = _load()
    before = len(crons)
    crons = [c for c in crons if c["name"] != args["name"]]
    if len(crons) == before:
        return ToolResult(
            content=[
                {
                    "type": "text",
                    "text": f"Cron '{args['name']}' not found.",
                }
            ],
            is_error=True,
        )
    _save(crons)
    return ToolResult(
        content=[
            {"type": "text", "text": f"Cron '{args['name']}' deleted."}
        ]
    )


async def _list(args: dict, ctx) -> ToolResult:
    crons = _load()
    if not crons:
        return ToolResult(
            content=[{"type": "text", "text": "No crons configured."}]
        )
    lines = [f"{c['name']} | {c['schedule']} | {c['prompt'][:60]}" for c in crons]
    return ToolResult(
        content=[{"type": "text", "text": "\n".join(lines)}]
    )


CRON_CREATE = build_tool(
    Tool(
        name="CronCreate",
        description="Create a scheduled recurring prompt (cron job).",
        input_schema=_CREATE_SCHEMA,
        call=_create,
        search_hint="cron schedule recurring job timer",
    )
)

CRON_DELETE = build_tool(
    Tool(
        name="CronDelete",
        description="Delete a scheduled cron job by name.",
        input_schema=_DELETE_SCHEMA,
        call=_delete,
        search_hint="cron delete remove cancel schedule",
    )
)

CRON_LIST = build_tool(
    Tool(
        name="CronList",
        description="List all configured cron jobs.",
        input_schema=_LIST_SCHEMA,
        call=_list,
        is_read_only=lambda _: True,
        search_hint="cron list schedule jobs",
    )
)
