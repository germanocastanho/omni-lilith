from __future__ import annotations

import os
from pathlib import Path

from src.tool import Tool, ToolResult, build_tool

_SCHEMA = {
    "type": "object",
    "properties": {
        "task": {
            "type": "string",
            "description": (
                "Full description of the task to execute inside the Nest "
                "multi-agent graph. Be specific and self-contained."
            ),
        },
        "model": {
            "type": "string",
            "description": (
                "Model override for this Nest run (default: claude-sonnet-4-6)."
            ),
        },
    },
    "required": ["task"],
}

_STORAGE = Path.home() / ".omni-lilith" / "nest"


async def _call(args: dict, ctx) -> ToolResult:
    from nest.executor import GraphExecutor, Runtime
    from nest.graph import LILITH_GOAL, LILITH_GRAPH
    from nest.llm import AnthropicLLM
    from nest.memory import get_memory_prompt
    from nest.nodes import DoneNode, HITLNode, JudgeNode, RouterNode
    from nest.tools.catalog import ALL_TOOLS, make_tool_executor

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    model = args.get("model") or LILITH_GRAPH.default_model
    task = args["task"]

    llm = AnthropicLLM(api_key=api_key, model=model)

    storage_path = _STORAGE / "sessions"
    storage_path.mkdir(parents=True, exist_ok=True)

    executor = GraphExecutor(
        runtime=Runtime(storage_path),
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

    result = await executor.execute(
        graph=LILITH_GRAPH,
        goal=LILITH_GOAL,
        input_data={"user_input": task},
    )

    if not result.success:
        return ToolResult(
            content=[{"type": "text", "text": f"Nest error: {result.error}"}],
            is_error=True,
        )

    output = result.output
    response = (
        output.get("task_result")
        or output.get("response")
        or "(Nest completed with no output)"
    )
    verdict = output.get("verdict", "PASS")

    text = f"[verdict={verdict}]\n{response}"
    return ToolResult(content=[{"type": "text", "text": text}])


TOOL = build_tool(
    Tool(
        name="NestRun",
        description=(
            "Launch a Nest multi-agent graph execution for tasks that require "
            "structured multi-step reasoning, human-in-the-loop authorization, "
            "or principled output validation via the Judge node. "
            "Do NOT use for routine tasks — prefer direct tools to save tokens. "
            "Invoke only when the task complexity justifies the graph overhead."
        ),
        input_schema=_SCHEMA,
        call=_call,
        is_concurrency_safe=lambda _: False,
        search_hint="nest multi-agent graph executor structured reasoning hitl",
    )
)
