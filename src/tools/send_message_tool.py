from src.tool import Tool, ToolResult, build_tool

_SCHEMA = {
    "type": "object",
    "properties": {
        "to": {
            "type": "string",
            "description": "Agent ID or name to send message to.",
        },
        "message": {
            "type": "string",
            "description": "The message content to send.",
        },
    },
    "required": ["to", "message"],
}

_message_queues: dict[str, list[str]] = {}


async def _call(args: dict, ctx) -> ToolResult:
    target = args["to"]
    msg = args["message"]
    _message_queues.setdefault(target, []).append(msg)
    return ToolResult(
        content=[
            {
                "type": "text",
                "text": f"Message sent to agent '{target}'.",
            }
        ]
    )


def get_messages(agent_id: str) -> list[str]:
    return _message_queues.pop(agent_id, [])


TOOL = build_tool(
    Tool(
        name="SendMessage",
        description=(
            "Send a message to a running agent by ID. "
            "The message is queued and delivered on the agent's next turn."
        ),
        input_schema=_SCHEMA,
        call=_call,
        search_hint="send message agent communicate notify",
    )
)
