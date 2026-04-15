from src.tool import Tool, ToolResult, build_tool

_SCHEMA = {
    "type": "object",
    "properties": {
        "method": {
            "type": "string",
            "description": (
                "LSP method, e.g. 'textDocument/definition', "
                "'textDocument/hover'."
            ),
        },
        "params": {
            "type": "object",
            "description": "LSP method parameters.",
        },
        "language_id": {
            "type": "string",
            "description": "Language ID, e.g. 'python', 'typescript'.",
        },
    },
    "required": ["method"],
}


async def _call(args: dict, ctx) -> ToolResult:
    return ToolResult(
        content=[
            {
                "type": "text",
                "text": (
                    "LSP integration not yet configured. "
                    "Start an LSP server and configure the connection."
                ),
            }
        ],
        is_error=True,
    )


TOOL = build_tool(
    Tool(
        name="LSP",
        description=(
            "Call an LSP (Language Server Protocol) method. "
            "Provides code intelligence: goto definition, hover, etc."
        ),
        input_schema=_SCHEMA,
        call=_call,
        search_hint="lsp language server definition hover completion",
    )
)
