from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.tool import Tool

type Messages = list[dict[str, Any]]
type AppState = dict[str, Any]


@dataclass
class ToolUseContext:
    model: str
    messages: Messages
    tools: list[Tool]
    system: str = ""
    verbose: bool = False
    max_tokens: int = 8192
    abort_event: asyncio.Event = field(default_factory=asyncio.Event)
    _app_state: AppState = field(default_factory=dict)
    agent_id: str | None = None
    plan_mode: bool = False

    def get_app_state(self) -> AppState:
        return self._app_state

    def set_app_state(self, updater: Any) -> None:
        if callable(updater):
            self._app_state = updater(self._app_state)
        else:
            self._app_state = updater

    def is_aborted(self) -> bool:
        return self.abort_event.is_set()

    def fork(self, extra_messages: Messages | None = None) -> ToolUseContext:
        return ToolUseContext(
            model=self.model,
            messages=list(self.messages) + (extra_messages or []),
            tools=self.tools,
            system=self.system,
            verbose=self.verbose,
            max_tokens=self.max_tokens,
            abort_event=self.abort_event,
            _app_state=dict(self._app_state),
            agent_id=self.agent_id,
            plan_mode=self.plan_mode,
        )
