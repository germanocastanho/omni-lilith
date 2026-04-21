from __future__ import annotations

import json
import logging
import re

from nest.types import NodeContext, NodeProtocol, NodeResult

from nest.identity import PRINCIPLES_SHORT

logger = logging.getLogger(__name__)

_JUDGE_PROMPT = f"""\
You are a principled judge evaluating an AI agent's output.

Your task: decide whether the output below respects these principles:
{PRINCIPLES_SHORT}

Return ONLY valid JSON:
{{
  "verdict": "PASS" | "WARN" | "BLOCK",
  "principle_at_issue": "I" | "II" | "III" | null,
  "reason": "<concise explanation>",
  "amendment": "<suggested amendment if WARN or BLOCK, otherwise null>"
}}
\
"""


def _extract_last_response(ctx: NodeContext) -> str:
    task_result = ctx.buffer.read("task_result")
    if task_result:
        return str(task_result)

    conv = getattr(ctx, "inherited_conversation", None)
    if conv is None:
        return ""
    messages = getattr(conv, "messages", [])
    for msg in reversed(messages):
        role = getattr(msg, "role", "")
        if role == "assistant":
            content = getattr(msg, "content", "")
            if content:
                return str(content)
    return ""


async def _judge(llm, output: str) -> dict:
    if not output.strip():
        return {
            "verdict": "PASS",
            "principle_at_issue": None,
            "reason": "No output to evaluate.",
            "amendment": None,
        }

    resp = await llm.acomplete(
        messages=[{
            "role": "user",
            "content": f"Output to evaluate:\n\n{output[:4000]}",
        }],
        system=_JUDGE_PROMPT,
        max_tokens=400,
    )
    text = resp.content.strip()
    m = re.search(r'\{[^{}]*"verdict"[^{}]*\}', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return {
        "verdict": "PASS",
        "principle_at_issue": None,
        "reason": "Judge parse error; defaulting to PASS.",
        "amendment": None,
    }


class JudgeNode(NodeProtocol):
    async def execute(self, ctx: NodeContext) -> NodeResult:
        output = _extract_last_response(ctx)

        if ctx.llm is None:
            verdict_data = {
                "verdict": "PASS",
                "principle_at_issue": None,
                "reason": "No LLM for judge; defaulting to PASS.",
                "amendment": None,
            }
        else:
            verdict_data = await _judge(ctx.llm, output)

        verdict = verdict_data.get("verdict", "PASS")
        reason = verdict_data.get("reason", "")
        amendment = verdict_data.get("amendment")
        principle = verdict_data.get("principle_at_issue")

        logger.info(
            "[judge] verdict=%s principle=%s reason=%s",
            verdict, principle, reason,
        )

        ctx.buffer.write("verdict", verdict, validate=False)
        ctx.buffer.write("verdict_reason", reason, validate=False)
        if amendment:
            ctx.buffer.write("verdict_amendment", amendment, validate=False)

        success = verdict in ("PASS", "WARN")

        return NodeResult(
            success=success,
            output={
                "verdict": verdict,
                "verdict_reason": reason,
                "verdict_amendment": amendment,
                "principle_at_issue": principle,
            },
            error=None if success else f"Principle violation: {reason}",
        )
