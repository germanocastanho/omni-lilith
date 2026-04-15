from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_MEMORY_PATH = Path.home() / ".omni-lilith" / "memory" / "ltm.json"

_EMPTY: dict[str, Any] = {
    "facts": {},
    "preferences": {},
    "session_notes": [],
    "user_context": {},
}


def _load() -> dict[str, Any]:
    if not _MEMORY_PATH.exists():
        return dict(_EMPTY)
    try:
        return json.loads(_MEMORY_PATH.read_text())
    except Exception:
        logger.warning("LTM: could not read memory file, starting fresh")
        return dict(_EMPTY)


def _save(data: dict[str, Any]) -> None:
    _MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = _MEMORY_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    tmp.replace(_MEMORY_PATH)


def read_memory(key: str) -> str:
    data = _load()
    for section in ("facts", "preferences", "user_context"):
        if key in data.get(section, {}):
            return str(data[section][key])
    return ""


def write_memory(section: str, key: str, value: str) -> None:
    if section not in ("facts", "preferences", "user_context"):
        section = "facts"
    data = _load()
    data.setdefault(section, {})[key] = value
    _save(data)


def append_note(note: str) -> None:
    data = _load()
    notes: list[str] = data.setdefault("session_notes", [])
    notes.append(note)
    if len(notes) > 100:
        notes[:] = notes[-100:]
    _save(data)


def get_memory_prompt() -> str:
    data = _load()
    parts: list[str] = []

    if data.get("facts"):
        lines = [f"  {k}: {v}" for k, v in list(data["facts"].items())[:20]]
        parts.append("Known facts:\n" + "\n".join(lines))

    if data.get("preferences"):
        lines = [f"  {k}: {v}" for k, v in list(data["preferences"].items())[:10]]
        parts.append("User preferences:\n" + "\n".join(lines))

    if data.get("user_context"):
        lines = [f"  {k}: {v}" for k, v in list(data["user_context"].items())[:10]]
        parts.append("User context:\n" + "\n".join(lines))

    if data.get("session_notes"):
        recent = data["session_notes"][-5:]
        parts.append("Recent session notes:\n" + "\n".join(f"  - {n}" for n in recent))

    if not parts:
        return ""
    return "<long_term_memory>\n" + "\n\n".join(parts) + "\n</long_term_memory>"


def dump_all() -> dict[str, Any]:
    return _load()
