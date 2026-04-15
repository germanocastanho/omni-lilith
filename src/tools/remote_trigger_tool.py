import httpx

from src.tool import Tool, ToolResult, build_tool

_SCHEMA = {
    "type": "object",
    "properties": {
        "url": {
            "type": "string",
            "description": "Endpoint URL to POST to.",
        },
        "payload": {
            "type": "object",
            "description": "JSON payload to send.",
        },
        "headers": {
            "type": "object",
            "description": "Optional HTTP headers.",
        },
    },
    "required": ["url"],
}


async def _call(args: dict, ctx) -> ToolResult:
    url = args["url"]
    payload = args.get("payload", {})
    headers = args.get("headers", {})

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
    except Exception as exc:
        return ToolResult(
            content=[{"type": "text", "text": str(exc)}],
            is_error=True,
        )

    try:
        body = resp.json()
        import json as _json
        text = _json.dumps(body, indent=2, ensure_ascii=False)
    except Exception:
        text = resp.text

    return ToolResult(
        content=[
            {
                "type": "text",
                "text": f"HTTP {resp.status_code}\n{text}",
            }
        ]
    )


TOOL = build_tool(
    Tool(
        name="RemoteTrigger",
        description=(
            "Send an HTTP POST to a remote endpoint. "
            "Used to trigger external webhooks or remote agents."
        ),
        input_schema=_SCHEMA,
        call=_call,
        search_hint="http post webhook trigger remote endpoint",
    )
)
