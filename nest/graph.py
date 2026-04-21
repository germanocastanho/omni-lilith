from __future__ import annotations

from nest.spec import (
    EdgeCondition,
    EdgeSpec,
    Goal,
    GraphSpec,
    NodeSpec,
)

from nest.identity import LILITH_IDENTITY

# ── Goal ──────────────────────────────────────────────────────────────────────

LILITH_GOAL = Goal(
    id="omni-lilith",
    name="Omni Lilith",
    description=(
        "Semi-autonomous AI agent: intellectually fierce, philosophically "
        "grounded, bounded only by humanity, the user's will, and legality."
    ),
    success_criteria=[
        {
            "id": "response_delivered",
            "description": "A substantive response or task result was produced",
            "metric": "custom",
            "target": "any",
        }
    ],
)

# ── Node system prompts (Layer 2) ─────────────────────────────────────────────

_CONV_PROMPT = """\
You are in conversational mode.
Engage with the user's message with your full intellectual depth.
Draw on memory, reason from first principles, be direct.
When you have delivered a complete response, call set_output("response", "<your response>").
Do not repeat yourself across tool calls.\
"""

_TASK_PROMPT = """\
You are in task-execution mode.
Execute the requested task autonomously using all available tools.
Think step by step. Use bash, file tools, or web fetch as needed.
If you determine that the task falls outside your directive scope or
violates your principles, call set_output("scope_escalation", "true")
and briefly explain via set_output("escalation_reason", "<reason>").
Otherwise, when the task is complete, call set_output("task_result", "<summary>").\
"""

# ── Node specifications ───────────────────────────────────────────────────────

_ROUTER = NodeSpec(
    id="router",
    name="Router",
    description="Classifies the user's message and routes to the appropriate node.",
    node_type="event_loop",
    input_keys=["user_input"],
    output_keys=["route_decision", "route_reason"],
    max_node_visits=0,
)

_CONVERSATION = NodeSpec(
    id="conversation",
    name="Conversation",
    description="Deep, contextual dialogue node. Lilith converses with the user.",
    node_type="event_loop",
    input_keys=["user_input"],
    output_keys=["response"],
    nullable_output_keys=["response"],
    system_prompt=_CONV_PROMPT,
    tools=[
        "ltm_read", "ltm_write", "ltm_note", "web_fetch",
    ],
    skip_judge=True,
    max_node_visits=0,
)

_TASK_EXECUTOR = NodeSpec(
    id="task_executor",
    name="Task Executor",
    description=(
        "Autonomous task execution. Runs tools, writes code, browses the web. "
        "Escalates if the task exceeds directive scope."
    ),
    node_type="event_loop",
    input_keys=["user_input"],
    output_keys=["task_result"],
    nullable_output_keys=["scope_escalation", "escalation_reason"],
    system_prompt=_TASK_PROMPT,
    tools=[
        "bash", "read_file", "write_file", "edit_file",
        "glob", "grep", "web_fetch",
        "ltm_read", "ltm_write", "ltm_note",
    ],
    max_node_visits=0,
)

_HITL = NodeSpec(
    id="hitl",
    name="Human-in-the-Loop",
    description=(
        "Pauses execution and requests human authorisation for actions "
        "outside Lilith's autonomous scope."
    ),
    node_type="event_loop",
    input_keys=["escalation_reason"],
    output_keys=["approved", "human_decision"],
    max_node_visits=0,
)

_JUDGE = NodeSpec(
    id="judge",
    name="Judge",
    description=(
        "Evaluates Lilith's output against her three supreme principles. "
        "Produces a PASS / WARN / BLOCK verdict."
    ),
    node_type="event_loop",
    input_keys=[],
    output_keys=["verdict", "verdict_reason"],
    nullable_output_keys=["verdict_amendment", "principle_at_issue"],
    max_node_visits=0,
)

_DONE = NodeSpec(
    id="done",
    name="Done",
    description="Terminal node. Finalises the turn.",
    node_type="event_loop",
    input_keys=[],
    output_keys=[],
    max_node_visits=0,
)

ALL_NODES = [_ROUTER, _CONVERSATION, _TASK_EXECUTOR, _HITL, _JUDGE, _DONE]

# ── Edges ─────────────────────────────────────────────────────────────────────

_EDGES = [
    # router → conversation
    EdgeSpec(
        id="router-to-conversation",
        source="router",
        target="conversation",
        condition=EdgeCondition.CONDITIONAL,
        condition_expr="route_decision == 'conversation'",
        input_mapping={"user_input": "user_input"},
        priority=10,
    ),
    # router → task_executor
    EdgeSpec(
        id="router-to-task",
        source="router",
        target="task_executor",
        condition=EdgeCondition.CONDITIONAL,
        condition_expr="route_decision == 'task'",
        input_mapping={"user_input": "user_input"},
        priority=10,
    ),
    # router → hitl (direct)
    EdgeSpec(
        id="router-to-hitl",
        source="router",
        target="hitl",
        condition=EdgeCondition.CONDITIONAL,
        condition_expr="route_decision == 'hitl'",
        input_mapping={"user_input": "user_input"},
        priority=10,
    ),
    # conversation → judge
    EdgeSpec(
        id="conversation-to-judge",
        source="conversation",
        target="judge",
        condition=EdgeCondition.ON_SUCCESS,
    ),
    # task_executor → hitl  (scope escalation)
    EdgeSpec(
        id="task-to-hitl",
        source="task_executor",
        target="hitl",
        condition=EdgeCondition.CONDITIONAL,
        condition_expr="scope_escalation == 'true' or scope_escalation == True",
        input_mapping={"escalation_reason": "escalation_reason"},
        priority=10,
    ),
    # task_executor → judge  (normal completion)
    EdgeSpec(
        id="task-to-judge",
        source="task_executor",
        target="judge",
        condition=EdgeCondition.CONDITIONAL,
        condition_expr=(
            "scope_escalation != 'true' and scope_escalation != True"
        ),
        priority=5,
    ),
    # hitl → task_executor  (approved)
    EdgeSpec(
        id="hitl-approved-to-task",
        source="hitl",
        target="task_executor",
        condition=EdgeCondition.CONDITIONAL,
        condition_expr="approved == True",
        input_mapping={"user_input": "user_input"},
        priority=10,
    ),
    # hitl → judge  (denied)
    EdgeSpec(
        id="hitl-denied-to-judge",
        source="hitl",
        target="judge",
        condition=EdgeCondition.CONDITIONAL,
        condition_expr="approved != True",
        priority=5,
    ),
    # judge → done
    EdgeSpec(
        id="judge-to-done",
        source="judge",
        target="done",
        condition=EdgeCondition.ON_SUCCESS,
    ),
    # judge failure → done  (still terminal, just flag it)
    EdgeSpec(
        id="judge-fail-to-done",
        source="judge",
        target="done",
        condition=EdgeCondition.ON_FAILURE,
    ),
]

# ── GraphSpec ─────────────────────────────────────────────────────────────────

LILITH_GRAPH = GraphSpec(
    id="omni-lilith-graph",
    goal_id=LILITH_GOAL.id,
    version="1.0.0",
    entry_node="router",
    terminal_nodes=["done"],
    pause_nodes=["hitl"],
    nodes=ALL_NODES,
    edges=_EDGES,
    conversation_mode="continuous",
    identity_prompt=LILITH_IDENTITY,
    default_model="claude-sonnet-4-6",
    loop_config={
        "max_iterations": 64,
        "max_tool_calls_per_turn": 32,
    },
    description=(
        "Omni Lilith — semi-autonomous agent with layered directives, "
        "LTM memory, and a principled judge."
    ),
)
