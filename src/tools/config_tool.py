import json
from pathlib import Path
from typing import Any

from src.tool import Tool, ToolResult, build_tool

_CONFIG_PATH = Path(".omni-lilith/config.json")

_SCHEMA = {
    "type": "object",
    "properties": {
        "key": {
            "type": "string",
            "description": "Config key to read or write.",
        },
        "value": {
            "description": "Value to set. Omit to read the current value.",
        },
    },
    "required": ["key"],
}


def _load() -> dict[str, Any]:
    if _CONFIG_PATH.exists():
        try:
            return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save(data: dict[str, Any]) -> None:
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CONFIG_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


async def _call(args: dict, ctx) -> ToolResult:
    key = args["key"]
    data = _load()

    if "value" not in args:
        val = data.get(key)
        if val is None:
            return ToolResult(
                content=[
                    {"type": "text", "text": f"Key '{key}' not set."}
                ]
            )
        return ToolResult(
            content=[
                {
                    "type": "text",
                    "text": json.dumps(val, ensure_ascii=False),
                }
            ]
        )

    data[key] = args["value"]
    _save(data)
    return ToolResult(
        content=[
            {"type": "text", "text": f"Config '{key}' updated."}
        ]
    )


TOOL = build_tool(
    Tool(
        name="Config",
        description=(
            "Read or write a configuration key in .omni-lilith/config.json. "
            "Omit value to read, include value to write."
        ),
        input_schema=_SCHEMA,
        call=_call,
        search_hint="config settings read write key value",
    )
)
