from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from nest.spec import EdgeCondition, EdgeSpec, GraphSpec, Goal, NodeSpec
from nest.types import DataBuffer, NodeContext, NodeProtocol, NodeResult, Tool, ToolUse

logger = logging.getLogger(__name__)

_DOOM_WINDOW = 3  # consecutive identical tool-call fingerprints → abort


def _fingerprint(tool_uses: list[dict]) -> list[tuple[str, str]]:
    result = []
    for tu in tool_uses:
        name = tu.get("name", "")
        try:
            canonical = json.dumps(tu.get("input", {}), sort_keys=True, default=str)
        except (TypeError, ValueError):
            canonical = str(tu.get("input", {}))
        result.append((name, canonical))
    return result


def _is_doom_loop(history: list[list[tuple[str, str]]]) -> bool:
    if len(history) < _DOOM_WINDOW:
        return False
    window = history[-_DOOM_WINDOW:]
    first = window[0]
    return bool(first) and all(fp == first for fp in window[1:])


@dataclass
class ExecutionResult:
    success: bool
    error: str | None = None
    output: dict[str, Any] = field(default_factory=dict)


class Runtime:
    def __init__(self, storage_path: Path) -> None:
        self._path = Path(storage_path)
        self._history_file = self._path / "history.json"

    def load_history(self) -> list[dict]:
        if self._history_file.exists():
            try:
                return json.loads(self._history_file.read_text())
            except Exception:
                return []
        return []

    def save_history(self, history: list[dict]) -> None:
        self._history_file.write_text(
            json.dumps(history, indent=2, ensure_ascii=False)
        )


def _tool_to_api(tool: Tool) -> dict:
    return {
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.parameters,
    }


_SET_OUTPUT: dict = {
    "name": "set_output",
    "description": (
        "Signal completion of this node. Store a key/value output. "
        "Call once per output key; call multiple times for multiple outputs."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "Output key name."},
            "value": {"type": "string", "description": "Output value."},
        },
        "required": ["key", "value"],
    },
}


class EventLoopNode:
    def __init__(
        self,
        spec: NodeSpec,
        identity_prompt: str,
        all_tools: list[Tool],
        tool_executor: Callable,
        llm: Any,
        max_tool_calls: int,
    ) -> None:
        self._spec = spec
        self._system = f"{identity_prompt}\n\n{spec.system_prompt or ''}".strip()
        self._api_tools = [
            _tool_to_api(t) for t in all_tools if t.name in spec.tools
        ] + [_SET_OUTPUT]
        self._tool_executor = tool_executor
        self._llm = llm
        self._max_tool_calls = max_tool_calls

    async def execute(
        self,
        ctx: NodeContext,
        history: list[dict],
    ) -> NodeResult:
        user_input = ctx.buffer.read("user_input") or ""
        messages: list[dict] = list(history)
        if user_input:
            messages.append({"role": "user", "content": user_input})

        done = False
        tool_fp_history: list[list[tuple[str, str]]] = []

        for _ in range(self._max_tool_calls):
            resp = await self._llm.acomplete(
                messages=messages,
                system=self._system,
                max_tokens=4096,
                tools=self._api_tools,
                echo=True,
            )

            logger.debug(
                "[event_loop] node=%s in=%d out=%d",
                self._spec.id,
                resp.input_tokens,
                resp.output_tokens,
            )

            assistant_content: list[dict] = []
            if resp.content:
                assistant_content.append({"type": "text", "text": resp.content})
            for tu in resp.tool_uses:
                assistant_content.append({
                    "type": "tool_use",
                    "id": tu["id"],
                    "name": tu["name"],
                    "input": tu["input"],
                })
            if assistant_content:
                messages.append({"role": "assistant", "content": assistant_content})

            if not resp.tool_uses:
                break

            # Doom loop detection
            fp = _fingerprint(resp.tool_uses)
            tool_fp_history.append(fp)
            if _is_doom_loop(tool_fp_history):
                logger.warning(
                    "[event_loop] doom loop detected in node=%s, aborting",
                    self._spec.id,
                )
                ctx.buffer.write(
                    "doom_loop_error",
                    f"Aborted: {_DOOM_WINDOW} identical tool-call sequences detected.",
                    validate=False,
                )
                break

            tool_results: list[dict] = []
            for tu in resp.tool_uses:
                if tu["name"] == "set_output":
                    key = tu["input"].get("key", "")
                    value = tu["input"].get("value", "")
                    ctx.buffer.write(key, value, validate=False)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tu["id"],
                        "content": "ok",
                    })
                    done = True
                else:
                    tool_use_obj = ToolUse(
                        id=tu["id"],
                        name=tu["name"],
                        input=tu["input"],
                    )
                    result = await self._tool_executor(tool_use_obj)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tu["id"],
                        "content": result.content,
                        "is_error": result.is_error,
                    })

            messages.append({"role": "user", "content": tool_results})

            if done:
                break

        return NodeResult(success=True, output=ctx.buffer.as_dict())


def _eval_condition(expr: str, state: dict) -> bool:
    try:
        return bool(eval(expr, {"__builtins__": {}}, state))  # noqa: S307
    except Exception:
        return False


def _next_node(
    edges: list[EdgeSpec],
    current: str,
    success: bool,
    buffer: DataBuffer,
) -> str | None:
    state = buffer.as_dict()
    candidates = sorted(
        [e for e in edges if e.source == current],
        key=lambda e: -e.priority,
    )
    for edge in candidates:
        if edge.condition == EdgeCondition.ON_SUCCESS and success:
            return edge.target
        if edge.condition == EdgeCondition.ON_FAILURE and not success:
            return edge.target
        if (
            edge.condition == EdgeCondition.CONDITIONAL
            and edge.condition_expr
            and _eval_condition(edge.condition_expr, state)
        ):
            return edge.target
    return None


class GraphExecutor:
    def __init__(
        self,
        runtime: Runtime,
        llm: Any,
        tools: list[Tool],
        tool_executor: Callable,
        node_registry: dict[str, NodeProtocol],
        storage_path: Path,
        dynamic_memory_provider: Callable[[], str] | None = None,
        loop_config: dict | None = None,
    ) -> None:
        self._runtime = runtime
        self._llm = llm
        self._tools = tools
        self._tool_executor = tool_executor
        self._registry = node_registry
        self._memory_provider = dynamic_memory_provider
        cfg = loop_config or {}
        self._max_tool_calls: int = cfg.get("max_tool_calls_per_turn", 32)
        self._max_iterations: int = cfg.get("max_iterations", 64)

    async def execute(
        self,
        graph: GraphSpec,
        goal: Goal,
        input_data: dict[str, Any],
    ) -> ExecutionResult:
        history = self._runtime.load_history()

        identity = graph.identity_prompt
        if self._memory_provider:
            mem_ctx = self._memory_provider()
            if mem_ctx:
                identity = f"{identity}\n\n## Long-Term Memory\n{mem_ctx}"

        buffer = DataBuffer()
        for k, v in input_data.items():
            buffer.write(k, v, validate=False)

        current: str | None = graph.entry_node
        iterations = 0

        while current and current not in graph.terminal_nodes:
            if iterations >= self._max_iterations:
                return ExecutionResult(
                    success=False,
                    error=f"Max iterations ({self._max_iterations}) reached",
                )
            iterations += 1
            logger.info("[executor] node=%s iter=%d", current, iterations)

            node_spec = next((n for n in graph.nodes if n.id == current), None)

            if current in self._registry:
                ctx = NodeContext(
                    input_data=dict(buffer.as_dict()),
                    buffer=buffer,
                    llm=self._llm,
                )
                result = await self._registry[current].execute(ctx)

            elif node_spec and node_spec.node_type == "event_loop":
                event_node = EventLoopNode(
                    spec=node_spec,
                    identity_prompt=identity,
                    all_tools=self._tools,
                    tool_executor=self._tool_executor,
                    llm=self._llm,
                    max_tool_calls=self._max_tool_calls,
                )
                ctx = NodeContext(
                    input_data=dict(buffer.as_dict()),
                    buffer=buffer,
                    llm=self._llm,
                )
                result = await event_node.execute(ctx, history)

            else:
                return ExecutionResult(
                    success=False,
                    error=f"Unknown node: {current}",
                )

            for k, v in (result.output or {}).items():
                buffer.write(k, v, validate=False)

            current = _next_node(graph.edges, current, result.success, buffer)

        user_input = input_data.get("user_input", "")
        if user_input:
            response = buffer.read("task_result") or buffer.read("response") or ""
            saved = self._runtime.load_history()
            saved.append({"role": "user", "content": user_input})
            if response:
                saved.append({"role": "assistant", "content": str(response)})
            self._runtime.save_history(saved)

        return ExecutionResult(success=True, output=buffer.as_dict())
