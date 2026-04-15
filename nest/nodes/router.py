from __future__ import annotations

import json
import logging
import re

from framework.graph.node import NodeContext, NodeProtocol, NodeResult

from nest.identity import PRINCIPLES_SHORT

logger = logging.getLogger(__name__)

_ROUTER_PROMPT = f"""\
You are a request classifier for a semi-autonomous AI agent.

Classify the user message into exactly one of:
  "conversation" — dialogue, questions, explanations, philosophy, analysis
  "task"         — actions: run code, edit files, shell commands, web searches,
                   autonomously completing multi-step work
  "hitl"         — requests that are ambiguous, ethically sensitive, potentially
                   risky, or that appear to conflict with the agent's principles

Principles context:
{PRINCIPLES_SHORT}

Respond with ONLY valid JSON: {{"route": "<decision>", "reason": "<brief reason>"}}\
"""


async def _classify(llm, user_input: str) -> tuple[str, str]:
    resp = await llm.acomplete(
        messages=[{"role": "user", "content": f"Input to classify:\n{user_input}"}],
        system=_ROUTER_PROMPT,
        max_tokens=150,
    )
    text = resp.content.strip()
    m = re.search(r'\{[^{}]*"route"[^{}]*\}', text, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group())
            route = str(data.get("route", "conversation")).lower()
            reason = str(data.get("reason", ""))
            if route in ("conversation", "task", "hitl"):
                return route, reason
        except json.JSONDecodeError:
            pass
    return "conversation", "fallback classification"


class RouterNode(NodeProtocol):
    async def execute(self, ctx: NodeContext) -> NodeResult:
        user_input = (
            ctx.input_data.get("user_input")
            or ctx.buffer.read("user_input")
            or ""
        )

        if not user_input.strip():
            return NodeResult(
                success=False,
                error="No user input provided",
            )

        ctx.buffer.write("user_input", user_input, validate=False)

        if ctx.llm is None:
            route, reason = "conversation", "no LLM available"
        else:
            route, reason = await _classify(ctx.llm, user_input)

        logger.info("[router] route=%s reason=%s", route, reason)
        ctx.buffer.write("route_decision", route, validate=False)
        ctx.buffer.write("route_reason", reason, validate=False)

        return NodeResult(
            success=True,
            output={
                "route_decision": route,
                "route_reason": reason,
                "user_input": user_input,
            },
        )
