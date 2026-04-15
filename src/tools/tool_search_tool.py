from __future__ import annotations

from src.tool import Tool, ToolResult, build_tool

_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": (
                "Keyword(s) or tool name to search for. "
                "Use 'select:ToolA,ToolB' to fetch specific tools by name."
            ),
        },
        "max_results": {
            "type": "integer",
            "description": "Max tools to return (default 5).",
        },
    },
    "required": ["query"],
}


async def _call(args: dict, ctx) -> ToolResult:
    query = args["query"].strip()
    max_results = int(args.get("max_results", 5))

    tools = ctx.tools

    if query.startswith("select:"):
        names = [n.strip() for n in query[7:].split(",")]
        matched = [
            t for t in tools
            if t.name in names or any(a in names for a in (t.aliases or []))
        ]
    else:
        terms = query.lower().split()
        scored: list[tuple[int, Tool]] = []
        for t in tools:
            score = 0
            haystack = (
                t.name.lower()
                + " "
                + t.description.lower()
                + " "
                + t.search_hint.lower()
            )
            for term in terms:
                if term in haystack:
                    score += 1
            if score:
                scored.append((score, t))
        scored.sort(key=lambda x: -x[0])
        matched = [t for _, t in scored[:max_results]]

    if not matched:
        return ToolResult(
            content=[{"type": "text", "text": "No matching tools found."}]
        )

    lines = []
    for t in matched[:max_results]:
        lines.append(
            f"**{t.name}** — {t.description[:80]}"
            + (f" [{t.search_hint}]" if t.search_hint else "")
        )

    return ToolResult(
        content=[{"type": "text", "text": "\n".join(lines)}]
    )


TOOL = build_tool(
    Tool(
        name="ToolSearch",
        description=(
            "Search available tools by name or keyword. "
            "Use 'select:ToolA,ToolB' to load specific tools by name."
        ),
        input_schema=_SCHEMA,
        call=_call,
        is_read_only=lambda _: True,
        search_hint="find tool search keyword discover",
    )
)
