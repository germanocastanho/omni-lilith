#!/usr/bin/env python3
"""MCP Sequential Thinking Server."""

import json
import os
import sys
from typing import Optional

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("sequential-thinking-server")

# In-memory state per process (one session per server instance)
_thought_history: list[dict] = []
_branches: dict[str, list[dict]] = {}
_disable_logging = os.environ.get("DISABLE_THOUGHT_LOGGING", "").lower() == "true"


def _format_thought(data: dict) -> str:
    num = data["thoughtNumber"]
    total = data["totalThoughts"]
    thought = data["thought"]
    is_revision = data.get("isRevision", False)
    revises = data.get("revisesThought")
    branch_from = data.get("branchFromThought")
    branch_id = data.get("branchId")

    if is_revision:
        prefix = f"Revision {num}/{total} (revising thought {revises})"
    elif branch_from:
        prefix = f"Branch {num}/{total} (from thought {branch_from}, ID: {branch_id})"
    else:
        prefix = f"Thought {num}/{total}"

    border = "─" * (max(len(prefix), len(thought)) + 4)
    return (
        f"\n┌{border}┐\n"
        f"│ {prefix} │\n"
        f"├{border}┤\n"
        f"│ {thought.ljust(len(border) - 2)} │\n"
        f"└{border}┘"
    )


@mcp.tool()
def sequentialthinking(
    thought: str,
    nextThoughtNeeded: bool,
    thoughtNumber: int,
    totalThoughts: int,
    isRevision: Optional[bool] = None,
    revisesThought: Optional[int] = None,
    branchFromThought: Optional[int] = None,
    branchId: Optional[str] = None,
    needsMoreThoughts: Optional[bool] = None,
) -> dict:
    """A detailed tool for dynamic and reflective problem-solving through thoughts.

    This tool helps analyze problems through a flexible thinking process that can
    adapt and evolve. Each thought can build on, question, or revise previous
    insights as understanding deepens.

    When to use this tool:
    - Breaking down complex problems into steps
    - Planning and design with room for revision
    - Analysis that might need course correction
    - Problems where the full scope might not be clear initially
    - Tasks that need to maintain context over multiple steps

    Parameters:
    - thought: Your current thinking step
    - nextThoughtNeeded: True if you need more thinking
    - thoughtNumber: Current number in sequence (1-based)
    - totalThoughts: Current estimate of thoughts needed
    - isRevision: Whether this thought revises previous thinking
    - revisesThought: Which thought number is being reconsidered
    - branchFromThought: Branching point thought number
    - branchId: Branch identifier
    - needsMoreThoughts: If more thoughts are needed beyond totalThoughts
    """
    if thoughtNumber > totalThoughts:
        totalThoughts = thoughtNumber

    data = {
        "thought": thought,
        "thoughtNumber": thoughtNumber,
        "totalThoughts": totalThoughts,
        "nextThoughtNeeded": nextThoughtNeeded,
        "isRevision": isRevision,
        "revisesThought": revisesThought,
        "branchFromThought": branchFromThought,
        "branchId": branchId,
        "needsMoreThoughts": needsMoreThoughts,
    }

    _thought_history.append(data)

    if branchFromThought and branchId:
        if branchId not in _branches:
            _branches[branchId] = []
        _branches[branchId].append(data)

    if not _disable_logging:
        print(_format_thought(data), file=sys.stderr)

    return {
        "thoughtNumber": thoughtNumber,
        "totalThoughts": totalThoughts,
        "nextThoughtNeeded": nextThoughtNeeded,
        "branches": list(_branches.keys()),
        "thoughtHistoryLength": len(_thought_history),
    }


if __name__ == "__main__":
    mcp.run()
