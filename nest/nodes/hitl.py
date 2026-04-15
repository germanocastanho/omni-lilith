from __future__ import annotations

import asyncio
import logging

from framework.graph.node import NodeContext, NodeProtocol, NodeResult

logger = logging.getLogger(__name__)

_APPROVE_TOKENS = {"y", "yes", "ok", "approve", "allow", "go", "do it", "sure"}
_DENY_TOKENS = {"n", "no", "deny", "reject", "stop", "abort", "cancel"}


class HITLNode(NodeProtocol):
    async def execute(self, ctx: NodeContext) -> NodeResult:
        reason = (
            ctx.buffer.read("escalation_reason")
            or ctx.input_data.get("escalation_reason")
            or "Lilith is requesting authorization for an action outside her scope."
        )
        extra = ctx.buffer.read("escalation_context") or ""

        banner = (
            "\n"
            "╔══════════════════════════════════════════════════════╗\n"
            "║  ⚑  HUMAN-IN-THE-LOOP — Authorization Required      ║\n"
            "╚══════════════════════════════════════════════════════╝\n"
        )
        print(banner)
        print(f"  Reason:  {reason}")
        if extra:
            print(f"  Context: {extra}")
        print()

        loop = asyncio.get_event_loop()
        try:
            raw = await loop.run_in_executor(
                None, lambda: input("  Approve? (y/n): ")
            )
        except (EOFError, KeyboardInterrupt):
            raw = "n"
        print()

        decision = raw.strip().lower()
        approved = decision in _APPROVE_TOKENS or (
            decision not in _DENY_TOKENS and decision.startswith("y")
        )

        logger.info("[hitl] decision=%r approved=%s", raw, approved)

        ctx.buffer.write("approved", approved, validate=False)
        ctx.buffer.write("human_decision", raw, validate=False)

        if not approved:
            ctx.buffer.write(
                "escalation_outcome",
                "Human denied the action.",
                validate=False,
            )

        return NodeResult(
            success=True,
            output={
                "approved": approved,
                "human_decision": raw,
            },
        )
