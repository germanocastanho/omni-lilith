from src.tool import Tool, ToolResult, build_tool

_LIST_SCHEMA = {
    "type": "object",
    "properties": {
        "server_name": {
            "type": "string",
            "description": "Name of the MCP server.",
        },
    },
    "required": ["server_name"],
}

_READ_SCHEMA = {
    "type": "object",
    "properties": {
        "server_name": {
            "type": "string",
            "description": "Name of the MCP server.",
        },
        "uri": {
            "type": "string",
            "description": "Resource URI to read.",
        },
    },
    "required": ["server_name", "uri"],
}


async def _list(args: dict, ctx) -> ToolResult:
    return ToolResult(
        content=[
            {
                "type": "text",
                "text": (
                    "MCP resource listing not yet implemented. "
                    "Configure MCP servers first."
                ),
            }
        ]
    )


async def _read(args: dict, ctx) -> ToolResult:
    return ToolResult(
        content=[
            {
                "type": "text",
                "text": (
                    "MCP resource reading not yet implemented. "
                    "Configure MCP servers first."
                ),
            }
        ]
    )


LIST_MCP_RESOURCES = build_tool(
    Tool(
        name="ListMcpResources",
        description="List available resources on an MCP server.",
        input_schema=_LIST_SCHEMA,
        call=_list,
        is_read_only=lambda _: True,
        search_hint="mcp resources list available server",
    )
)

READ_MCP_RESOURCE = build_tool(
    Tool(
        name="ReadMcpResource",
        description="Read a resource from an MCP server by URI.",
        input_schema=_READ_SCHEMA,
        call=_read,
        is_read_only=lambda _: True,
        search_hint="mcp resource read fetch uri",
    )
)
