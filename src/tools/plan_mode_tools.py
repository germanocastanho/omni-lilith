from src.tool import Tool, ToolResult, build_tool

_ENTER_SCHEMA = {
    "type": "object",
    "properties": {
        "plan": {
            "type": "string",
            "description": "The plan content to present to the user.",
        },
    },
    "required": [],
}

_EXIT_SCHEMA = {
    "type": "object",
    "properties": {
        "allowed_prompts": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Bash prompts that are pre-approved.",
        },
    },
    "required": [],
}


async def _enter(args: dict, ctx) -> ToolResult:
    ctx.plan_mode = True
    plan = args.get("plan", "")
    from rich.console import Console
    from rich.panel import Panel

    Console().print(
        Panel(plan or "Plan mode active.", title="[bold]Plan Mode[/]")
    )
    return ToolResult(
        content=[{"type": "text", "text": "Entered plan mode."}]
    )


async def _exit(args: dict, ctx) -> ToolResult:
    ctx.plan_mode = False
    return ToolResult(
        content=[{"type": "text", "text": "Exited plan mode."}]
    )


ENTER_PLAN_MODE = build_tool(
    Tool(
        name="EnterPlanMode",
        description=(
            "Enter plan mode. In this mode, only read-only tools are "
            "allowed. Use to present a plan before implementation."
        ),
        input_schema=_ENTER_SCHEMA,
        call=_enter,
        search_hint="plan mode read-only design architect",
    )
)

EXIT_PLAN_MODE = build_tool(
    Tool(
        name="ExitPlanMode",
        description=(
            "Exit plan mode and return to normal execution mode."
        ),
        input_schema=_EXIT_SCHEMA,
        call=_exit,
        search_hint="exit plan mode implement execute",
    )
)
