from pathlib import Path

from src.tool import Tool, ToolResult, build_tool

_SCHEMA = {
    "type": "object",
    "properties": {
        "file_path": {
            "type": "string",
            "description": "Absolute path to the file to edit.",
        },
        "old_string": {
            "type": "string",
            "description": (
                "The exact string to replace. Must be unique in the file."
            ),
        },
        "new_string": {
            "type": "string",
            "description": "The string to replace it with.",
        },
        "replace_all": {
            "type": "boolean",
            "description": (
                "Replace all occurrences instead of just the first."
            ),
        },
    },
    "required": ["file_path", "old_string", "new_string"],
}


async def _call(args: dict, ctx) -> ToolResult:
    path = Path(args["file_path"])
    if not path.exists():
        return ToolResult(
            content=[{"type": "text", "text": f"File not found: {path}"}],
            is_error=True,
        )

    old = args["old_string"]
    new = args["new_string"]
    replace_all = args.get("replace_all", False)

    text = path.read_text(encoding="utf-8", errors="replace")

    count = text.count(old)
    if count == 0:
        return ToolResult(
            content=[
                {
                    "type": "text",
                    "text": (
                        f"old_string not found in {path}. "
                        "Ensure exact match including whitespace."
                    ),
                }
            ],
            is_error=True,
        )

    if count > 1 and not replace_all:
        return ToolResult(
            content=[
                {
                    "type": "text",
                    "text": (
                        f"old_string found {count} times. "
                        "Add more context to make it unique, "
                        "or set replace_all=true."
                    ),
                }
            ],
            is_error=True,
        )

    if replace_all:
        updated = text.replace(old, new)
    else:
        updated = text.replace(old, new, 1)

    path.write_text(updated, encoding="utf-8")
    replaced = count if replace_all else 1
    return ToolResult(
        content=[
            {
                "type": "text",
                "text": (
                    f"Replaced {replaced} occurrence(s) in {path}"
                ),
            }
        ]
    )


TOOL = build_tool(
    Tool(
        name="Edit",
        description=(
            "Make exact string replacements in a file. "
            "old_string must be unique in the file unless replace_all=true. "
            "Read the file first to ensure old_string is correct."
        ),
        input_schema=_SCHEMA,
        call=_call,
        search_hint="edit modify replace string file patch",
    )
)
