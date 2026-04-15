import json
from pathlib import Path
from typing import Any

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from src.tool import Tool, ToolResult, build_tool

_CONFIG_PATH = Path.home() / ".omni-lilith" / "mcps.json"

_SCHEMA = {
    "type": "object",
    "properties": {
        "server_name": {
            "type": "string",
            "description": "Name of the MCP server to call.",
        },
        "tool_name": {
            "type": "string",
            "description": "Tool name on the MCP server.",
        },
        "arguments": {
            "type": "object",
            "description": "Arguments to pass to the MCP tool.",
        },
    },
    "required": ["server_name", "tool_name"],
}


def _load_config() -> dict[str, Any]:
    if not _CONFIG_PATH.exists():
        return {}
    return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))


async def _call_mcp(server_def: dict, tool_name: str, arguments: dict) -> str:
    command: str = server_def["command"]
    args: list[str] = server_def.get("args", [])
    env: dict | None = server_def.get("env")

    params = StdioServerParameters(command=command, args=args, env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
    parts = []
    for block in result.content:
        if hasattr(block, "text"):
            parts.append(block.text)
    return "\n".join(parts) if parts else "(no output)"


async def _call(args: dict, ctx) -> ToolResult:
    server_name: str = args["server_name"]
    tool_name: str = args["tool_name"]
    arguments: dict = args.get("arguments") or {}

    config = _load_config()
    if not config:
        return ToolResult(
            content=[{
                "type": "text",
                "text": (
                    f"No MCP servers configured. "
                    f"Add server definitions to {_CONFIG_PATH}."
                ),
            }],
            is_error=True,
        )

    server_def = config.get(server_name)
    if server_def is None:
        available = ", ".join(config.keys()) or "(none)"
        return ToolResult(
            content=[{
                "type": "text",
                "text": (
                    f"MCP server '{server_name}' not found. "
                    f"Available servers: {available}"
                ),
            }],
            is_error=True,
        )

    try:
        text = await _call_mcp(server_def, tool_name, arguments)
        return ToolResult(content=[{"type": "text", "text": text}])
    except Exception as exc:
        return ToolResult(
            content=[{"type": "text", "text": f"MCP error: {exc}"}],
            is_error=True,
        )


TOOL = build_tool(
    Tool(
        name="MCPTool",
        description=(
            "Call a tool on a connected MCP (Model Context Protocol) server. "
            "Servers are configured in ~/.omni-lilith/mcps.json."
        ),
        input_schema=_SCHEMA,
        call=_call,
        search_hint="mcp server protocol tool external",
    )
)
