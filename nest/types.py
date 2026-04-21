from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


class DataBuffer:
    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    def read(self, key: str) -> Any:
        return self._data.get(key)

    def write(self, key: str, value: Any, validate: bool = True) -> None:
        self._data[key] = value

    def as_dict(self) -> dict[str, Any]:
        return dict(self._data)


@dataclass
class NodeContext:
    input_data: dict[str, Any]
    buffer: DataBuffer
    llm: Any = None
    inherited_conversation: Any = None


@dataclass
class NodeResult:
    success: bool
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class NodeProtocol(ABC):
    @abstractmethod
    async def execute(self, ctx: NodeContext) -> NodeResult: ...


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolUse:
    id: str
    name: str
    input: dict[str, Any]


@dataclass
class ToolResult:
    tool_use_id: str
    content: str
    is_error: bool = False
