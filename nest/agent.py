from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

_console = Console()

_BANNER = """
 ██╗     ██╗██╗     ██╗████████╗██╗  ██╗
 ██║     ██║██║     ██║╚══██╔══╝██║  ██║
 ██║     ██║██║     ██║   ██║   ███████║
 ██║     ██║██║     ██║   ██║   ██╔══██║
 ███████╗██║███████╗██║   ██║   ██║  ██║
 ╚══════╝╚═╝╚══════╝╚═╝   ╚═╝   ╚═╝  ╚═╝
                    Omni — Nest Edition
"""

_STORAGE_PATH = Path.home() / ".omni-lilith" / "nest"


def _build_executor(model: str, verbose: bool):
    from nest.executor import GraphExecutor, Runtime
    from nest.graph import LILITH_GRAPH
    from nest.llm import AnthropicLLM
    from nest.memory import get_memory_prompt
    from nest.nodes import DoneNode, HITLNode, JudgeNode, RouterNode
    from nest.tools.catalog import ALL_TOOLS, make_tool_executor

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        _console.print("[bold red]Error:[/] API key not set. Check your .env file.")
        sys.exit(1)

    llm = AnthropicLLM(api_key=api_key, model=model)

    storage_path = _STORAGE_PATH / "sessions"
    storage_path.mkdir(parents=True, exist_ok=True)

    runtime = Runtime(storage_path=storage_path)

    executor = GraphExecutor(
        runtime=runtime,
        llm=llm,
        tools=ALL_TOOLS,
        tool_executor=make_tool_executor,
        node_registry={
            "router": RouterNode(),
            "judge": JudgeNode(),
            "hitl": HITLNode(),
            "done": DoneNode(),
        },
        storage_path=storage_path,
        dynamic_memory_provider=get_memory_prompt,
        loop_config=LILITH_GRAPH.loop_config,
    )

    return executor


async def run_turn(
    executor,
    user_input: str,
) -> dict:
    from nest.graph import LILITH_GOAL, LILITH_GRAPH

    result = await executor.execute(
        graph=LILITH_GRAPH,
        goal=LILITH_GOAL,
        input_data={"user_input": user_input},
    )
    return result


async def _repl(model: str, verbose: bool) -> None:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.styles import Style

    executor = _build_executor(model=model, verbose=verbose)

    _console.print(
        Panel(
            Text(_BANNER, style="bold magenta", justify="center"),
            subtitle="[dim]ctrl+c to interrupt | /exit to quit | /mem to show memory[/]",
            border_style="magenta",
        )
    )

    history_path = _STORAGE_PATH / "repl_history"
    history_path.parent.mkdir(parents=True, exist_ok=True)

    session: PromptSession = PromptSession(
        history=FileHistory(str(history_path)),
        style=Style.from_dict({"prompt": "bold magenta"}),
    )

    while True:
        try:
            user_input = await session.prompt_async("lilith> ")
        except (EOFError, KeyboardInterrupt):
            _console.print("\n[dim]Goodbye.[/]")
            break

        user_input = user_input.strip()
        if not user_input:
            continue

        if user_input in ("/exit", "/quit", "exit", "quit"):
            _console.print("[dim]Goodbye.[/]")
            break

        if user_input == "/mem":
            from nest.memory import dump_all
            import json
            _console.print(json.dumps(dump_all(), indent=2, ensure_ascii=False))
            continue

        if user_input == "/help":
            _console.print(
                "[bold]/exit[/] — quit\n"
                "[bold]/mem[/]  — show long-term memory\n"
                "[bold]/help[/] — this message"
            )
            continue

        try:
            result = await run_turn(executor, user_input)
            if result and not result.success and result.error:
                _console.print(f"[red]Error:[/] {result.error}")
        except KeyboardInterrupt:
            _console.print("\n[yellow]Interrupted.[/]")


def start_repl(
    model: str = os.environ.get("LILITH_MODEL", "claude-sonnet-4-6"),
    verbose: bool = False,
) -> None:
    if verbose:
        logging.basicConfig(level=logging.INFO)
    asyncio.run(_repl(model=model, verbose=verbose))
