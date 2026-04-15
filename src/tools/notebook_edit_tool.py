import json
from pathlib import Path

from src.tool import Tool, ToolResult, build_tool

_SCHEMA = {
    "type": "object",
    "properties": {
        "notebook_path": {
            "type": "string",
            "description": "Path to the .ipynb notebook file.",
        },
        "cell_index": {
            "type": "integer",
            "description": "0-based index of the cell to edit.",
        },
        "new_source": {
            "type": "string",
            "description": "New source content for the cell.",
        },
        "cell_type": {
            "type": "string",
            "enum": ["code", "markdown"],
            "description": "Cell type when inserting a new cell.",
        },
        "insert_after": {
            "type": "integer",
            "description": "Insert a new cell after this index (-1 = append).",
        },
    },
    "required": ["notebook_path"],
}


async def _call(args: dict, ctx) -> ToolResult:
    path = Path(args["notebook_path"])
    if not path.exists():
        return ToolResult(
            content=[
                {"type": "text", "text": f"Notebook not found: {path}"}
            ],
            is_error=True,
        )

    try:
        nb = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return ToolResult(
            content=[{"type": "text", "text": str(exc)}],
            is_error=True,
        )

    cells = nb.get("cells", [])

    if "insert_after" in args:
        idx = int(args["insert_after"])
        cell_type = args.get("cell_type", "code")
        new_cell = {
            "cell_type": cell_type,
            "source": args.get("new_source", ""),
            "metadata": {},
            "outputs": [] if cell_type == "code" else None,
        }
        if new_cell["outputs"] is None:
            del new_cell["outputs"]
        insert_pos = idx + 1 if idx >= 0 else len(cells)
        cells.insert(insert_pos, new_cell)
        nb["cells"] = cells
        path.write_text(json.dumps(nb, indent=1), encoding="utf-8")
        return ToolResult(
            content=[
                {
                    "type": "text",
                    "text": f"Inserted {cell_type} cell at index {insert_pos}.",
                }
            ]
        )

    if "cell_index" in args and "new_source" in args:
        idx = int(args["cell_index"])
        if idx >= len(cells):
            return ToolResult(
                content=[
                    {
                        "type": "text",
                        "text": (
                            f"Cell index {idx} out of range "
                            f"({len(cells)} cells)."
                        ),
                    }
                ],
                is_error=True,
            )
        cells[idx]["source"] = args["new_source"]
        nb["cells"] = cells
        path.write_text(json.dumps(nb, indent=1), encoding="utf-8")
        return ToolResult(
            content=[
                {"type": "text", "text": f"Cell {idx} updated."}
            ]
        )

    summary = "\n".join(
        f"[{i}] {c['cell_type']}: "
        f"{str(c.get('source', ''))[:60]!r}"
        for i, c in enumerate(cells)
    )
    return ToolResult(
        content=[{"type": "text", "text": summary or "(empty notebook)"}]
    )


TOOL = build_tool(
    Tool(
        name="NotebookEdit",
        description=(
            "Read or edit Jupyter notebook cells. "
            "Provide cell_index+new_source to edit, "
            "insert_after to insert a new cell, "
            "or just notebook_path to list cells."
        ),
        input_schema=_SCHEMA,
        call=_call,
        search_hint="jupyter notebook ipynb cell edit",
    )
)
