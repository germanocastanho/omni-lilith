from __future__ import annotations

import logging

from nest.types import NodeContext, NodeProtocol, NodeResult

import nest.memory as mem

logger = logging.getLogger(__name__)


class DoneNode(NodeProtocol):
    async def execute(self, ctx: NodeContext) -> NodeResult:
        verdict = ctx.buffer.read("verdict") or "PASS"
        response = ctx.buffer.read("task_result") or ""
        amendment = ctx.buffer.read("verdict_amendment")
        user_input = ctx.buffer.read("user_input") or ""

        if user_input:
            note = f"Q: {user_input[:120]} | verdict={verdict}"
            mem.append_note(note)

        out: dict = {"verdict": verdict}
        if response:
            out["final_response"] = str(response)[:200]
        if amendment:
            out["amendment"] = amendment

        return NodeResult(success=True, output=out)
