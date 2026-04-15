from src.tool import Tool, ToolResult, build_tool

_SCHEMA = {
    "type": "object",
    "properties": {
        "question": {
            "type": "string",
            "description": "The question to ask the user.",
        },
        "options": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional list of choices to present.",
        },
    },
    "required": ["question"],
}


async def _call(args: dict, ctx) -> ToolResult:
    from rich.console import Console
    from rich.prompt import Prompt

    console = Console()
    question = args["question"]
    options = args.get("options", [])

    console.print(f"\n[bold cyan]Question:[/] {question}")

    if options:
        for i, opt in enumerate(options, 1):
            console.print(f"  [dim]{i}.[/] {opt}")
        choices = [str(i) for i in range(1, len(options) + 1)]
        answer_idx = Prompt.ask(
            "Choose", choices=choices, default="1"
        )
        answer = options[int(answer_idx) - 1]
    else:
        answer = Prompt.ask("Your answer")

    return ToolResult(
        content=[{"type": "text", "text": answer}]
    )


TOOL = build_tool(
    Tool(
        name="AskUserQuestion",
        description=(
            "Ask the user a question and wait for their response. "
            "Use when you need clarification or a decision from the user."
        ),
        input_schema=_SCHEMA,
        call=_call,
        search_hint="ask user question input prompt clarify",
    )
)
