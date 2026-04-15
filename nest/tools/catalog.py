from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path
from typing import Any

from framework.llm.provider import Tool, ToolResult, ToolUse

import nest.memory as mem


# ── Tool definitions ────────────────────────────────────────────────────────

def _tool(name: str, description: str, props: dict, required: list[str]) -> Tool:
    return Tool(
        name=name,
        description=description,
        parameters={
            "type": "object",
            "properties": props,
            "required": required,
        },
    )


BASH = _tool(
    "bash",
    (
        "Execute a shell command. Use for running scripts, git, system tasks. "
        "Prefer dedicated file tools for file I/O."
    ),
    {
        "command": {"type": "string", "description": "Shell command to run."},
        "timeout": {
            "type": "number",
            "description": "Timeout in seconds (default 120, max 600).",
        },
    },
    ["command"],
)

READ_FILE = _tool(
    "read_file",
    "Read a file from disk. Returns its content as text.",
    {
        "path": {"type": "string", "description": "Absolute file path."},
        "offset": {"type": "integer", "description": "Start line (1-based)."},
        "limit": {"type": "integer", "description": "Number of lines to read."},
    },
    ["path"],
)

WRITE_FILE = _tool(
    "write_file",
    "Write content to a file, creating it if needed.",
    {
        "path": {"type": "string", "description": "Absolute file path."},
        "content": {"type": "string", "description": "Content to write."},
    },
    ["path", "content"],
)

EDIT_FILE = _tool(
    "edit_file",
    "Replace an exact string in a file. The old_string must be unique.",
    {
        "path": {"type": "string", "description": "Absolute file path."},
        "old_string": {"type": "string", "description": "Text to replace."},
        "new_string": {"type": "string", "description": "Replacement text."},
    },
    ["path", "old_string", "new_string"],
)

GLOB = _tool(
    "glob",
    "Find files matching a glob pattern.",
    {
        "pattern": {"type": "string", "description": "Glob pattern, e.g. '**/*.py'."},
        "base": {"type": "string", "description": "Base directory (default cwd)."},
    },
    ["pattern"],
)

GREP = _tool(
    "grep",
    "Search file contents with a regex. Returns matching lines with context.",
    {
        "pattern": {"type": "string", "description": "Regex pattern."},
        "path": {"type": "string", "description": "File or directory to search."},
        "context": {"type": "integer", "description": "Lines of context (default 2)."},
    },
    ["pattern"],
)

WEB_FETCH = _tool(
    "web_fetch",
    "Fetch the text content of a URL.",
    {
        "url": {"type": "string", "description": "URL to fetch."},
        "timeout": {"type": "number", "description": "Timeout in seconds (default 30)."},
    },
    ["url"],
)

LTM_READ = _tool(
    "ltm_read",
    "Read a value from long-term memory by key.",
    {"key": {"type": "string", "description": "Memory key to look up."}},
    ["key"],
)

LTM_WRITE = _tool(
    "ltm_write",
    (
        "Write a value into long-term memory. "
        "Sections: 'facts', 'preferences', 'user_context'."
    ),
    {
        "section": {
            "type": "string",
            "enum": ["facts", "preferences", "user_context"],
            "description": "Memory section.",
        },
        "key": {"type": "string", "description": "Memory key."},
        "value": {"type": "string", "description": "Value to store."},
    },
    ["section", "key", "value"],
)

LTM_NOTE = _tool(
    "ltm_note",
    "Append a brief note to the session notes in long-term memory.",
    {"note": {"type": "string", "description": "Note text."}},
    ["note"],
)

ALL_TOOLS: list[Tool] = [
    BASH,
    READ_FILE,
    WRITE_FILE,
    EDIT_FILE,
    GLOB,
    GREP,
    WEB_FETCH,
    LTM_READ,
    LTM_WRITE,
    LTM_NOTE,
]

CONVERSATION_TOOLS: list[Tool] = [LTM_READ, LTM_WRITE, LTM_NOTE, WEB_FETCH]
TASK_TOOLS: list[Tool] = ALL_TOOLS


def build_tool_catalog(
    include_execution: bool = True,
) -> list[Tool]:
    if include_execution:
        return ALL_TOOLS
    return CONVERSATION_TOOLS


# ── Executors ────────────────────────────────────────────────────────────────

async def _exec_bash(inp: dict[str, Any]) -> str:
    cmd = inp["command"]
    timeout = min(float(inp.get("timeout", 120)), 600.0)
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_b, stderr_b = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
        out = stdout_b.decode(errors="replace")
        err = stderr_b.decode(errors="replace")
        parts = []
        if out:
            parts.append(out[:50_000])
        if err:
            parts.append(f"<stderr>\n{err[:10_000]}\n</stderr>")
        code = proc.returncode or 0
        if code != 0:
            parts.append(f"<exit_code>{code}</exit_code>")
        return "\n".join(parts) or "(no output)"
    except asyncio.TimeoutError:
        return f"<error>Command timed out after {timeout}s</error>"
    except Exception as exc:
        return f"<error>{exc}</error>"


def _exec_read_file(inp: dict[str, Any]) -> str:
    path = Path(inp["path"])
    if not path.exists():
        return f"<error>File not found: {path}</error>"
    try:
        lines = path.read_text(errors="replace").splitlines()
        offset = max(0, int(inp.get("offset", 1)) - 1)
        limit = int(inp.get("limit", len(lines)))
        chunk = lines[offset: offset + limit]
        numbered = "\n".join(
            f"{offset + i + 1}\t{line}" for i, line in enumerate(chunk)
        )
        return numbered or "(empty file)"
    except Exception as exc:
        return f"<error>{exc}</error>"


def _exec_write_file(inp: dict[str, Any]) -> str:
    path = Path(inp["path"])
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(inp["content"])
        return f"Written {len(inp['content'])} chars to {path}"
    except Exception as exc:
        return f"<error>{exc}</error>"


def _exec_edit_file(inp: dict[str, Any]) -> str:
    path = Path(inp["path"])
    if not path.exists():
        return f"<error>File not found: {path}</error>"
    try:
        text = path.read_text()
        old = inp["old_string"]
        new = inp["new_string"]
        if old not in text:
            return f"<error>old_string not found in {path}</error>"
        if text.count(old) > 1:
            return f"<error>old_string is not unique ({text.count(old)} occurrences)</error>"
        path.write_text(text.replace(old, new, 1))
        return f"Edit applied to {path}"
    except Exception as exc:
        return f"<error>{exc}</error>"


def _exec_glob(inp: dict[str, Any]) -> str:
    import glob as _glob
    base = inp.get("base", ".")
    pattern = inp["pattern"]
    try:
        matches = sorted(_glob.glob(pattern, root_dir=base, recursive=True))
        if not matches:
            return "(no matches)"
        return "\n".join(matches[:500])
    except Exception as exc:
        return f"<error>{exc}</error>"


def _exec_grep(inp: dict[str, Any]) -> str:
    pattern = inp["pattern"]
    path = inp.get("path", ".")
    context = int(inp.get("context", 2))
    try:
        args = ["grep", "-rn", f"--context={context}", pattern, path]
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=30
        )
        output = result.stdout[:50_000]
        return output or "(no matches)"
    except Exception as exc:
        return f"<error>{exc}</error>"


async def _exec_web_fetch(inp: dict[str, Any]) -> str:
    import httpx
    url = inp["url"]
    timeout = float(inp.get("timeout", 30))
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text[:50_000]
    except Exception as exc:
        return f"<error>{exc}</error>"


def _exec_ltm_read(inp: dict[str, Any]) -> str:
    val = mem.read_memory(inp["key"])
    return val if val else "(not found)"


def _exec_ltm_write(inp: dict[str, Any]) -> str:
    mem.write_memory(inp["section"], inp["key"], inp["value"])
    return f"Stored {inp['section']}/{inp['key']}"


def _exec_ltm_note(inp: dict[str, Any]) -> str:
    mem.append_note(inp["note"])
    return "Note appended."


async def make_tool_executor(tool_use: ToolUse) -> ToolResult:
    name = tool_use.name
    inp = tool_use.input

    is_error = False
    try:
        if name == "bash":
            content = await _exec_bash(inp)
            is_error = "<exit_code>" in content or "<error>" in content
        elif name == "read_file":
            content = _exec_read_file(inp)
            is_error = content.startswith("<error>")
        elif name == "write_file":
            content = _exec_write_file(inp)
            is_error = content.startswith("<error>")
        elif name == "edit_file":
            content = _exec_edit_file(inp)
            is_error = content.startswith("<error>")
        elif name == "glob":
            content = _exec_glob(inp)
        elif name == "grep":
            content = _exec_grep(inp)
        elif name == "web_fetch":
            content = await _exec_web_fetch(inp)
            is_error = content.startswith("<error>")
        elif name == "ltm_read":
            content = _exec_ltm_read(inp)
        elif name == "ltm_write":
            content = _exec_ltm_write(inp)
        elif name == "ltm_note":
            content = _exec_ltm_note(inp)
        else:
            content = f"<error>Unknown tool: {name}</error>"
            is_error = True
    except Exception as exc:
        content = f"<error>{exc}</error>"
        is_error = True

    return ToolResult(
        tool_use_id=tool_use.id,
        content=content,
        is_error=is_error,
    )
