from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class EdgeCondition(Enum):
    CONDITIONAL = "conditional"
    ON_SUCCESS = "on_success"
    ON_FAILURE = "on_failure"


@dataclass
class Goal:
    id: str
    name: str
    description: str
    success_criteria: list[dict] = field(default_factory=list)


@dataclass
class NodeSpec:
    id: str
    name: str
    description: str
    node_type: str
    input_keys: list[str]
    output_keys: list[str]
    nullable_output_keys: list[str] = field(default_factory=list)
    system_prompt: str | None = None
    tools: list[str] = field(default_factory=list)
    skip_judge: bool = False
    max_node_visits: int = 0


@dataclass
class EdgeSpec:
    id: str
    source: str
    target: str
    condition: EdgeCondition
    condition_expr: str | None = None
    input_mapping: dict[str, str] = field(default_factory=dict)
    priority: int = 0


@dataclass
class GraphSpec:
    id: str
    goal_id: str
    version: str
    entry_node: str
    terminal_nodes: list[str]
    pause_nodes: list[str]
    nodes: list[NodeSpec]
    edges: list[EdgeSpec]
    conversation_mode: str
    identity_prompt: str
    default_model: str
    loop_config: dict
    description: str = ""
