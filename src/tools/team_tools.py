import json
from pathlib import Path
from typing import Any

from src.tool import Tool, ToolResult, build_tool

_TEAMS_PATH = Path(".omni-lilith/teams.json")

_CREATE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "Team name."},
        "agents": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of agent type names in the team.",
        },
        "description": {
            "type": "string",
            "description": "What this team is for.",
        },
    },
    "required": ["name", "agents"],
}

_DELETE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "Team name to delete."},
    },
    "required": ["name"],
}


def _load() -> list[dict[str, Any]]:
    if _TEAMS_PATH.exists():
        try:
            return json.loads(_TEAMS_PATH.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save(teams: list[dict[str, Any]]) -> None:
    _TEAMS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _TEAMS_PATH.write_text(
        json.dumps(teams, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


async def _create(args: dict, ctx) -> ToolResult:
    teams = _load()
    if any(t["name"] == args["name"] for t in teams):
        return ToolResult(
            content=[
                {
                    "type": "text",
                    "text": f"Team '{args['name']}' already exists.",
                }
            ],
            is_error=True,
        )
    teams.append(
        {
            "name": args["name"],
            "agents": args["agents"],
            "description": args.get("description", ""),
        }
    )
    _save(teams)
    return ToolResult(
        content=[
            {
                "type": "text",
                "text": (
                    f"Team '{args['name']}' created with "
                    f"{len(args['agents'])} agents."
                ),
            }
        ]
    )


async def _delete(args: dict, ctx) -> ToolResult:
    teams = _load()
    before = len(teams)
    teams = [t for t in teams if t["name"] != args["name"]]
    if len(teams) == before:
        return ToolResult(
            content=[
                {
                    "type": "text",
                    "text": f"Team '{args['name']}' not found.",
                }
            ],
            is_error=True,
        )
    _save(teams)
    return ToolResult(
        content=[
            {"type": "text", "text": f"Team '{args['name']}' deleted."}
        ]
    )


TEAM_CREATE = build_tool(
    Tool(
        name="TeamCreate",
        description="Create a named team of agents.",
        input_schema=_CREATE_SCHEMA,
        call=_create,
        search_hint="team create group agents multi",
    )
)

TEAM_DELETE = build_tool(
    Tool(
        name="TeamDelete",
        description="Delete a team by name.",
        input_schema=_DELETE_SCHEMA,
        call=_delete,
        search_hint="team delete remove group",
    )
)
