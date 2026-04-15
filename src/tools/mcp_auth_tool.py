from src.tool import Tool, ToolResult, build_tool

_SCHEMA = {
    "type": "object",
    "properties": {
        "server_name": {
            "type": "string",
            "description": "Name of the MCP server to authenticate with.",
        },
        "token": {
            "type": "string",
            "description": "Authentication token (OAuth or API key).",
        },
    },
    "required": ["server_name"],
}


async def _call(args: dict, ctx) -> ToolResult:
    return ToolResult(
        content=[
            {
                "type": "text",
                "text": (
                    "MCP authentication not yet configured. "
                    "Set up OAuth credentials in .omni-lilith/mcp_auth.json."
                ),
            }
        ],
        is_error=True,
    )


TOOL = build_tool(
    Tool(
        name="McpAuth",
        description="Authenticate with an MCP server.",
        input_schema=_SCHEMA,
        call=_call,
        search_hint="mcp auth oauth authenticate server",
    )
)
