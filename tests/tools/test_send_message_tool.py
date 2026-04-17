import src.tools.send_message_tool as msg_mod
from src.tools.send_message_tool import _call, get_messages


def _clear_queues():
    msg_mod._message_queues.clear()


async def test_sends_message_to_queue(ctx):
    _clear_queues()
    result = await _call({"to": "agent-1", "message": "hello"}, ctx)
    assert not result.is_error
    assert "agent-1" in result.content[0]["text"]
    assert msg_mod._message_queues["agent-1"] == ["hello"]


async def test_get_messages_returns_and_clears(ctx):
    _clear_queues()
    await _call({"to": "a", "message": "msg1"}, ctx)
    await _call({"to": "a", "message": "msg2"}, ctx)
    msgs = get_messages("a")
    assert msgs == ["msg1", "msg2"]
    assert get_messages("a") == []


async def test_get_messages_unknown_agent(ctx):
    _clear_queues()
    assert get_messages("nobody") == []


async def test_multiple_agents_isolated(ctx):
    _clear_queues()
    await _call({"to": "a1", "message": "for a1"}, ctx)
    await _call({"to": "a2", "message": "for a2"}, ctx)
    assert get_messages("a1") == ["for a1"]
    assert get_messages("a2") == ["for a2"]
