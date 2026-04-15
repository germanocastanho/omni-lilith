from pathlib import Path

from src.tool import Tool, ToolResult, build_tool

_SKILLS_DIR = Path("skills")

_SCHEMA = {
    "type": "object",
    "properties": {
        "skill": {
            "type": "string",
            "description": (
                "Skill name to execute (subdirectory name), "
                "or omit to list available skills."
            ),
        },
        "args": {
            "type": "string",
            "description": "Optional arguments passed to the skill.",
        },
    },
    "required": [],
}


async def _call(args: dict, ctx) -> ToolResult:
    skill_name = args.get("skill")

    if not skill_name:
        if not _SKILLS_DIR.exists():
            return ToolResult(
                content=[
                    {"type": "text", "text": "No skills directory found."}
                ]
            )
        skills = [d.name for d in sorted(_SKILLS_DIR.iterdir()) if d.is_dir() and (d / "SKILL.md").exists()]
        if not skills:
            return ToolResult(
                content=[{"type": "text", "text": "No skills available."}]
            )
        return ToolResult(
            content=[
                {
                    "type": "text",
                    "text": "Available skills:\n" + "\n".join(f"- {n}" for n in skills),
                }
            ]
        )

    skill_path = _SKILLS_DIR / skill_name / "SKILL.md"
    if not skill_path.exists():
        return ToolResult(
            content=[
                {
                    "type": "text",
                    "text": f"Skill '{skill_name}' not found.",
                }
            ],
            is_error=True,
        )

    prompt = skill_path.read_text(encoding="utf-8")
    if args.get("args"):
        prompt += f"\n\nArgs: {args['args']}"

    from src.query_engine import run_query

    sub = ctx.fork(extra_messages=[{"role": "user", "content": prompt}])
    sub.messages = [{"role": "user", "content": prompt}]
    result = await run_query(sub)

    return ToolResult(
        content=[{"type": "text", "text": result or "(no output)"}]
    )


TOOL = build_tool(
    Tool(
        name="Skill",
        description=(
            "Execute a skill defined in skills/<name>/SKILL.md. "
            "Omit skill name to list all available skills."
        ),
        input_schema=_SCHEMA,
        call=_call,
        search_hint="skill execute prompt macro command",
    )
)
